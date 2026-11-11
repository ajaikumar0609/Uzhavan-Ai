import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/localization/l10n.dart';
import '../../../core/localization/locale_controller.dart';
import '../../../core/networking/api_failure.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_tokens.dart';
import '../../../shared/utils/failure_text.dart';
import '../../../shared/utils/links.dart';
import '../../../shared/widgets/app_scaffold.dart';
import '../../../shared/widgets/ui_kit.dart';
import '../../farm/presentation/selected_farm.dart';
import '../data/voice_services.dart';
import 'chat_controller.dart';

/// Localized text for a failed answer. Never raw server/exception text.
String assistantErrorText(AppLocalizations l, ApiFailure f) {
  if (f.code == ApiFailure.networkCode) return l.errServerUnreachable;
  return switch (f.kind) {
    ApiFailureKind.rateLimited => rateLimitText(l, f.retryAfter),
    ApiFailureKind.unauthenticated => l.errSessionExpired,
    ApiFailureKind.unavailable => l.assistantUnavailable,
    _ => l.assistantError,
  };
}

String stageText(AppLocalizations l, String? stage) => switch (stage) {
      'intent_detected' => l.stageUnderstanding,
      'planning' => l.stagePlanning,
      'tool_complete' => l.stageGathering,
      'evidence_ready' => l.stageEvidence,
      'grounding' => l.stageGrounding,
      'reasoning' || 'response_complete' || 'token' => l.stageWriting,
      _ => l.stageStarting,
    };

class AssistantScreen extends ConsumerStatefulWidget {
  const AssistantScreen({super.key});

  @override
  ConsumerState<AssistantScreen> createState() => _AssistantScreenState();
}

class _AssistantScreenState extends ConsumerState<AssistantScreen> with WidgetsBindingObserver {
  final _input = TextEditingController();
  final _scroll = ScrollController();
  bool _listening = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _input.dispose();
    _scroll.dispose();
    super.dispose();
  }

  /// Background/foreground: release the microphone and stop speech when the app leaves the
  /// foreground, so nothing keeps listening or talking behind the farmer's back.
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) return;
    final chat = ref.read(chatProvider.notifier);
    ref.read(voiceInputProvider).cancel();
    chat.stopSpeaking();
    if (_listening) {
      if (mounted) setState(() => _listening = false);
      chat.endVoiceTurn();
    }
  }

  bool get _english => ref.read(localeProvider).languageCode == AppLocales.english.languageCode;

  void _send([String? text]) {
    final q = (text ?? _input.text).trim();
    if (q.isEmpty) return;
    _input.clear();
    // Typed questions are spoken back only when Voice Conversation Mode is on.
    ref.read(chatProvider.notifier).send(q, isVoiceInput: false);
    _scrollToEnd();
  }

  void _scrollToEnd() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent,
            duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
      }
    });
  }

  Future<void> _toggleMic() async {
    final chat = ref.read(chatProvider.notifier);
    final voice = ref.read(voiceInputProvider);
    final localeId = _english ? 'en-IN' : 'ta-IN';

    // Microphone activation always cuts any speech first (no mic/TTS overlap).
    await chat.stopSpeaking();

    if (_listening) {
      // Tap again = finish the utterance now; the final transcript is submitted automatically.
      await voice.stop();
      return;
    }
    final result = await voice.init(localeId: localeId);
    if (!mounted) return;
    final notice = switch (result) {
      VoiceInitResult.ready => VoiceNotice.none,
      VoiceInitResult.permissionDenied => VoiceNotice.micPermission,
      VoiceInitResult.offlineUnavailable => VoiceNotice.offlineUnavailable,
      VoiceInitResult.offlineLanguageMissing => VoiceNotice.offlineLanguageMissing,
      VoiceInitResult.notAvailable => VoiceNotice.sttError,
    };
    if (notice != VoiceNotice.none) {
      chat.endVoiceTurn(notice: notice); // no audio captured; text input remains available
      return;
    }
    chat.beginVoiceTurn();
    setState(() => _listening = true);
    try {
      await voice.start(
        localeId: localeId,
        onResult: (text, isFinal) {
          if (!mounted) return;
          _input.value = TextEditingValue(text: text, selection: TextSelection.collapsed(offset: text.length));
          if (isFinal) {
            _input.clear();
            chat.sendVoice(text); // once per turn; empty/duplicate ignored by the controller
            _scrollToEnd();
          }
        },
        onDone: () {
          if (!mounted) return;
          setState(() => _listening = false);
          _input.clear();
          // No transcript was submitted (silence / cancelled): back to idle. If one was, the
          // controller is already THINKING and this is a no-op.
          chat.endVoiceTurn();
        },
        onError: (code) {
          if (!mounted) return;
          chat.endVoiceTurn(
            notice: switch (code) {
              'offline_unavailable' => VoiceNotice.offlineUnavailable,
              'language_missing' => VoiceNotice.offlineLanguageMissing,
              'permission' => VoiceNotice.micPermission,
              _ => VoiceNotice.sttError,
            },
          );
        },
      );
    } catch (_) {
      if (!mounted) return;
      setState(() => _listening = false);
      chat.endVoiceTurn(notice: VoiceNotice.sttError);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final c = context.colors;
    final chat = ref.watch(chatProvider);
    final voiceState = ref.watch(assistantVoiceStateProvider);
    final voiceModeEnabled = ref.watch(voiceConversationEnabledProvider);
    final voiceNotice = ref.watch(voiceNoticeProvider);
    ref.listen(chatProvider, (_, _) => _scrollToEnd());
    return AppScaffold(
      title: l.featureAssistant,
      automaticallyImplyLeading: false,
      actions: [
        IconButton(
          key: const Key('voice-mode-toggle'),
          tooltip: voiceModeEnabled ? l.voiceModeOn : l.voiceModeOff,
          isSelected: voiceModeEnabled,
          style: IconButton.styleFrom(
            backgroundColor: voiceModeEnabled ? c.primarySoft : null,
            foregroundColor: voiceModeEnabled ? c.secondary : c.mutedForeground,
          ),
          icon: Icon(voiceModeEnabled ? Icons.record_voice_over_rounded : Icons.voice_over_off_outlined),
          onPressed: () => ref.read(voiceConversationEnabledProvider.notifier).toggle(),
        ),
        if (chat.messages.isNotEmpty)
          IconButton(
            tooltip: l.assistantNewChat,
            icon: const Icon(Icons.add_comment_outlined),
            onPressed: chat.busy ? null : () => ref.read(chatProvider.notifier).clear(),
          ),
      ],
      body: Column(
        children: [
          const Padding(
            padding: EdgeInsets.fromLTRB(AppSpace.page, AppSpace.sm, AppSpace.page, 0),
            child: FarmPicker(),
          ),
          Expanded(
            child: chat.messages.isEmpty
                ? _EmptyChat(onAsk: _send)
                : ListView.builder(
                    controller: _scroll,
                    padding: const EdgeInsets.fromLTRB(AppSpace.md, AppSpace.md, AppSpace.md, AppSpace.md),
                    itemCount: chat.messages.length,
                    itemBuilder: (context, i) => MessageBubble(
                      message: chat.messages[i],
                      isLast: i == chat.messages.length - 1,
                    ),
                  ),
          ),
          if (voiceNotice != VoiceNotice.none) _VoiceNoticeBanner(notice: voiceNotice),
          if (voiceState != AssistantVoiceState.idle && voiceState != AssistantVoiceState.error)
            _VoiceStateBar(state: voiceState),
          _Composer(
            controller: _input,
            listening: _listening,
            busy: chat.busy,
            onMic: _toggleMic,
            onSend: _send,
          ),
        ],
      ),
    );
  }
}

/// First-run view: what the assistant is for, and questions that work today.
class _EmptyChat extends StatelessWidget {
  const _EmptyChat({required this.onAsk});
  final void Function([String? text]) onAsk;

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final c = context.colors;
    final t = Theme.of(context).textTheme;
    final suggestions = <(IconData, String)>[
      (Icons.grass_rounded, l.suggest1),
      (Icons.water_drop_outlined, l.suggest2),
      (Icons.account_balance_outlined, l.suggest3),
      (Icons.terrain_outlined, l.suggest4),
    ];
    return ListView(
      padding: const EdgeInsets.fromLTRB(AppSpace.page, AppSpace.xl, AppSpace.page, AppSpace.lg),
      children: [
        const Align(alignment: AlignmentDirectional.centerStart, child: IconTile(Icons.eco_rounded, size: 52)),
        const SizedBox(height: AppSpace.lg),
        Text(l.assistantEmptyTitle, style: t.headlineSmall),
        const SizedBox(height: AppSpace.xs),
        Text(l.assistantIntro, style: t.bodyLarge?.copyWith(color: c.mutedForeground)),
        const SizedBox(height: AppSpace.xxl),
        Text(l.assistantSuggestions, style: t.labelMedium?.copyWith(color: c.mutedForeground)),
        const SizedBox(height: AppSpace.sm),
        for (final (icon, text) in suggestions)
          Padding(
            padding: const EdgeInsets.only(bottom: AppSpace.sm),
            child: AppCard(
              raised: false,
              padding: const EdgeInsets.symmetric(horizontal: AppSpace.md, vertical: AppSpace.md),
              onTap: () => onAsk(text),
              child: Row(
                children: [
                  Icon(icon, size: 20, color: c.secondary),
                  const SizedBox(width: AppSpace.md),
                  Expanded(child: Text(text, style: t.bodyLarge)),
                  Icon(Icons.north_east_rounded, size: 18, color: c.mutedForeground),
                ],
              ),
            ),
          ),
      ],
    );
  }
}

/// Listening / thinking / speaking. While speaking, Stop is a distinct, always-visible control.
class _VoiceStateBar extends ConsumerWidget {
  const _VoiceStateBar({required this.state});
  final AssistantVoiceState state;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final c = context.colors;
    final t = Theme.of(context).textTheme;
    final speaking = state == AssistantVoiceState.speaking;
    final thinking = state == AssistantVoiceState.thinking;
    final (ink, bg, border) = (thinking ? Tone.caution : Tone.brand).resolve(c);
    void stop() => ref.read(chatProvider.notifier).stopSpeaking();
    return Padding(
      padding: const EdgeInsets.fromLTRB(AppSpace.md, 2, AppSpace.md, AppSpace.xs),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          key: const Key('voice-state-banner'),
          borderRadius: AppRadius.control,
          onTap: speaking ? stop : null,
          child: Container(
            padding: const EdgeInsets.fromLTRB(AppSpace.md, AppSpace.sm, AppSpace.sm, AppSpace.sm),
            decoration: BoxDecoration(color: bg, borderRadius: AppRadius.control, border: Border.all(color: border)),
            child: Row(
              children: [
                Icon(
                  speaking ? Icons.graphic_eq_rounded : (thinking ? Icons.auto_awesome_rounded : Icons.mic_rounded),
                  size: 20,
                  color: ink,
                ),
                const SizedBox(width: AppSpace.sm + 2),
                Expanded(
                  child: Text(
                    speaking
                        ? '${l.voiceSpeaking} · ${l.voiceTapToStop}'
                        : (thinking ? l.voiceThinking : l.voiceListening),
                    style: t.labelLarge?.copyWith(color: ink),
                  ),
                ),
                if (speaking)
                  FilledButton.icon(
                    key: const Key('stop-speaking-button'),
                    style: FilledButton.styleFrom(
                      backgroundColor: c.danger,
                      foregroundColor: c.dangerForeground,
                      minimumSize: const Size(0, 40),
                      padding: const EdgeInsets.symmetric(horizontal: AppSpace.md),
                      textStyle: t.labelLarge,
                    ),
                    onPressed: stop,
                    icon: const Icon(Icons.stop_rounded, size: 18),
                    label: Text(l.voiceStop),
                  )
                else
                  Padding(
                    padding: const EdgeInsets.all(AppSpace.md),
                    child: SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: ink)),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// The input bar: microphone, text field, send. Sits above the keyboard.
class _Composer extends StatelessWidget {
  const _Composer({
    required this.controller,
    required this.listening,
    required this.busy,
    required this.onMic,
    required this.onSend,
  });

  final TextEditingController controller;
  final bool listening;
  final bool busy;
  final VoidCallback onMic;
  final void Function([String? text]) onSend;

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final c = context.colors;
    return DecoratedBox(
      decoration: BoxDecoration(color: c.card, border: Border(top: BorderSide(color: c.border))),
      child: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(AppSpace.sm, AppSpace.sm, AppSpace.sm, AppSpace.sm),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              IconButton(
                key: const Key('mic-button'),
                tooltip: listening ? l.voiceStop : l.voiceStart,
                style: IconButton.styleFrom(
                  minimumSize: const Size(48, 48),
                  backgroundColor: listening ? c.danger.withValues(alpha: 0.12) : c.muted,
                  foregroundColor: listening ? c.danger : c.secondary,
                ),
                onPressed: busy ? null : onMic,
                icon: Icon(listening ? Icons.stop_rounded : Icons.mic_none_rounded),
              ),
              const SizedBox(width: AppSpace.sm),
              Expanded(
                child: TextField(
                  key: const Key('chat-input'),
                  controller: controller,
                  minLines: 1,
                  maxLines: 4,
                  textInputAction: TextInputAction.send,
                  textCapitalization: TextCapitalization.sentences,
                  onSubmitted: busy ? null : (_) => onSend(),
                  decoration: InputDecoration(
                    hintText: listening ? l.voiceListening : l.assistantHint,
                    fillColor: c.background,
                    contentPadding: const EdgeInsets.symmetric(horizontal: AppSpace.lg, vertical: AppSpace.md),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: BorderSide(color: c.border)),
                    enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: BorderSide(color: c.border)),
                    focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: BorderSide(color: c.secondary, width: 1.6)),
                  ),
                ),
              ),
              const SizedBox(width: AppSpace.sm),
              IconButton(
                key: const Key('send-button'),
                tooltip: l.assistantSend,
                style: IconButton.styleFrom(
                  minimumSize: const Size(48, 48),
                  backgroundColor: c.primary,
                  foregroundColor: c.primaryForeground,
                  disabledBackgroundColor: c.muted,
                  disabledForegroundColor: c.mutedForeground,
                ),
                onPressed: busy ? null : () => onSend(),
                icon: const Icon(Icons.arrow_upward_rounded),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// The label the backend prefixes to an answer that has no verified TNAU source. The UI shows
/// it as a badge instead of inline text; the wording and meaning are the backend's.
const _guidancePrefixes = <String>[
  'General guidance (not from TNAU sources): ',
  'பொது வழிகாட்டுதல் (TNAU ஆதாரம் இல்லாமல்): ',
];

(bool, String) splitGuidanceLabel(String text) {
  for (final p in _guidancePrefixes) {
    if (text.startsWith(p)) return (true, text.substring(p.length));
  }
  return (false, text);
}

class MessageBubble extends ConsumerWidget {
  const MessageBubble({super.key, required this.message, required this.isLast});
  final ChatMessage message;
  final bool isLast;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final c = context.colors;
    final t = Theme.of(context).textTheme;
    final user = message.role == ChatRole.user;
    final width = MediaQuery.sizeOf(context).width;

    if (user) {
      return Align(
        alignment: AlignmentDirectional.centerEnd,
        child: ConstrainedBox(
          constraints: BoxConstraints(maxWidth: width * 0.82),
          child: Container(
            margin: const EdgeInsets.only(top: AppSpace.sm, bottom: AppSpace.xs),
            padding: const EdgeInsets.symmetric(horizontal: AppSpace.lg, vertical: AppSpace.md),
            decoration: BoxDecoration(
              color: c.primary,
              borderRadius: const BorderRadiusDirectional.only(
                topStart: Radius.circular(20),
                topEnd: Radius.circular(20),
                bottomStart: Radius.circular(20),
                bottomEnd: Radius.circular(6),
              ),
            ),
            child: Text(message.text, style: t.bodyLarge?.copyWith(color: c.primaryForeground)),
          ),
        ),
      );
    }

    Widget content;
    Color border = c.border;
    if (message.pending) {
      content = Column(
        key: const Key('stage-indicator'),
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (message.text.isNotEmpty) ...[Text(message.text, style: t.bodyLarge), const SizedBox(height: AppSpace.sm)],
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: c.secondary)),
              const SizedBox(width: AppSpace.sm + 2),
              Flexible(child: Text(stageText(l, message.stage), style: t.bodyMedium?.copyWith(color: c.mutedForeground))),
            ],
          ),
          const SizedBox(height: AppSpace.sm),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: const SizedBox(width: 180, child: LinearProgressIndicator(minHeight: 3)),
          ),
        ],
      );
    } else if (message.isError) {
      border = c.danger.withValues(alpha: 0.45);
      content = Column(
        key: const Key('chat-error'),
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.error_outline_rounded, color: c.danger, size: 20),
              const SizedBox(width: AppSpace.sm),
              Expanded(child: Text(assistantErrorText(l, message.failure!), style: t.bodyLarge)),
            ],
          ),
          if (isLast) ...[
            const SizedBox(height: AppSpace.md),
            FilledButton.tonalIcon(
              key: const Key('chat-retry'),
              style: FilledButton.styleFrom(minimumSize: const Size(0, 44)),
              onPressed: () => ref.read(chatProvider.notifier).retry(),
              icon: const Icon(Icons.refresh_rounded, size: 18),
              label: Text(l.retry),
            ),
          ],
        ],
      );
    } else {
      final sources = message.sources;
      final fallback = message.isFallback == true;
      final (guidance, body) = splitGuidanceLabel(message.text);
      if (fallback) border = c.warning.withValues(alpha: 0.45);
      content = Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (guidance)
            Padding(
              padding: const EdgeInsets.only(bottom: AppSpace.sm),
              child: StatusBadge(
                key: const Key('chat-guidance-badge'),
                label: '${l.assistantGeneralGuidance} · ${l.assistantGeneralGuidanceNote}',
                tone: Tone.caution,
                icon: Icons.lightbulb_outline_rounded,
              ),
            ),
          if (fallback)
            Padding(
              padding: const EdgeInsets.only(bottom: AppSpace.sm),
              child: StatusBadge(
                label: l.assistantNoAnswerTitle,
                tone: Tone.caution,
                icon: Icons.shield_outlined,
              ),
            ),
          SelectableText(body, key: const Key('chat-answer'), style: t.bodyLarge),
          if (fallback)
            Padding(
              padding: const EdgeInsets.only(top: AppSpace.sm),
              child: Text(l.assistantFallbackNote, style: t.bodyMedium?.copyWith(color: c.warning)),
            ),
          if (sources != null && sources.isNotEmpty) ...[
            const SizedBox(height: AppSpace.md),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(AppSpace.md),
              decoration: BoxDecoration(color: c.primarySoft.withValues(alpha: 0.7), borderRadius: BorderRadius.circular(AppRadius.md)),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.library_books_outlined, size: 16, color: c.secondary),
                      const SizedBox(width: 6),
                      Text(l.assistantSources, key: const Key('chat-sources'), style: t.titleSmall?.copyWith(fontWeight: FontWeight.w700)),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(l.assistantSourcesNote, style: t.bodySmall),
                  const SizedBox(height: AppSpace.xs),
                  for (final s in sources)
                    s.url != null
                        ? LinkText(label: _sourceLabel(s), url: s.url)
                        : Padding(
                            padding: const EdgeInsets.only(top: AppSpace.xs),
                            child: Text('• ${_sourceLabel(s)}', style: t.bodyMedium),
                          ),
                ],
              ),
            ),
          ],
          const SizedBox(height: AppSpace.xs),
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              IconButton(
                tooltip: l.assistantCopy,
                visualDensity: VisualDensity.compact,
                icon: Icon(Icons.copy_rounded, size: 19, color: c.mutedForeground),
                onPressed: () async {
                  final messenger = ScaffoldMessenger.of(context);
                  await Clipboard.setData(ClipboardData(text: message.text));
                  messenger.showSnackBar(SnackBar(content: Text(l.assistantCopied), duration: const Duration(seconds: 2)));
                },
              ),
              SpeakButton(text: message.spokenText ?? message.text),
            ],
          ),
        ],
      );
    }
    return Align(
      alignment: AlignmentDirectional.centerStart,
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: width * 0.92),
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: AppSpace.xs),
          padding: const EdgeInsets.fromLTRB(AppSpace.lg, AppSpace.md, AppSpace.md, AppSpace.sm),
          decoration: BoxDecoration(
            color: c.card,
            border: Border.all(color: border),
            borderRadius: const BorderRadiusDirectional.only(
              topStart: Radius.circular(6),
              topEnd: Radius.circular(20),
              bottomStart: Radius.circular(20),
              bottomEnd: Radius.circular(20),
            ),
            boxShadow: AppShadows.card(c),
          ),
          child: content,
        ),
      ),
    );
  }

  static String _sourceLabel(ChatSource s) {
    final title = s.title;
    return title == null || title.isEmpty ? s.source : '${s.source}: $title';
  }
}

/// Reads a final answer aloud with the phone's own voice. While it is speaking the same
/// control becomes a clearly different Stop action.
class SpeakButton extends ConsumerStatefulWidget {
  const SpeakButton({super.key, required this.text});
  final String text;

  @override
  ConsumerState<SpeakButton> createState() => _SpeakButtonState();
}

class _SpeakButtonState extends ConsumerState<SpeakButton> {
  bool _speaking = false;

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final c = context.colors;
    return TextButton.icon(
      key: const Key('speak-button'),
      style: TextButton.styleFrom(
        foregroundColor: _speaking ? c.danger : c.secondary,
        visualDensity: VisualDensity.compact,
      ),
      icon: Icon(_speaking ? Icons.stop_circle_outlined : Icons.volume_up_outlined, size: 20),
      label: Text(_speaking ? l.voiceStop : l.voiceSpeakAnswer),
      onPressed: () async {
        final chat = ref.read(chatProvider.notifier);
        if (_speaking) {
          await chat.stopSpeaking();
          if (mounted) setState(() => _speaking = false);
          return;
        }
        setState(() => _speaking = true);
        // Same single-utterance path as auto-speak (stops anything already playing first).
        // A missing local voice is reported by the voice banner, not a transient snackbar.
        await chat.speakAnswer(widget.text);
        if (mounted) setState(() => _speaking = false);
      },
    );
  }
}

/// Explains a voice failure in plain language (never raw errors) with a dismiss action.
/// Text input stays available while it is shown.
class _VoiceNoticeBanner extends ConsumerWidget {
  const _VoiceNoticeBanner({required this.notice});
  final VoiceNotice notice;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final text = switch (notice) {
      VoiceNotice.micPermission => l.voicePermissionDenied,
      VoiceNotice.offlineUnavailable => l.voiceOfflineUnavailable,
      VoiceNotice.offlineLanguageMissing => l.voiceOfflineLanguageMissing,
      VoiceNotice.sttError => l.voiceSttError,
      VoiceNotice.ttsVoiceMissingTamil => l.voiceTtsMissingTamil,
      VoiceNotice.ttsVoiceMissingEnglish => l.voiceTtsMissingEnglish,
      VoiceNotice.ttsFailed => l.voiceTtsFailed,
      VoiceNotice.none => '',
    };
    return Padding(
      padding: const EdgeInsets.fromLTRB(AppSpace.md, AppSpace.xs, AppSpace.md, AppSpace.xs),
      child: NoticeBanner(
        key: const Key('voice-notice'),
        text: text,
        tone: Tone.critical,
        trailing: IconButton(
          key: const Key('voice-notice-dismiss'),
          visualDensity: VisualDensity.compact,
          tooltip: l.voiceDismiss,
          icon: const Icon(Icons.close_rounded, size: 18),
          onPressed: () {
            ref.read(voiceNoticeProvider.notifier).set(VoiceNotice.none);
            ref.read(assistantVoiceStateProvider.notifier).setState(AssistantVoiceState.idle);
          },
        ),
      ),
    );
  }
}
