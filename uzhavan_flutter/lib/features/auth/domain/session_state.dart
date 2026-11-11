import 'package:flutter/foundation.dart';

enum SessionStatus { restoring, signedOut, signedIn }

@immutable
class SessionState {
  const SessionState._(this.status, this.profileComplete, this.expired);

  const SessionState.restoring() : this._(SessionStatus.restoring, false, false);
  const SessionState.signedOut({bool expired = false})
      : this._(SessionStatus.signedOut, false, expired);
  const SessionState.signedIn({required bool profileComplete})
      : this._(SessionStatus.signedIn, profileComplete, false);

  final SessionStatus status;
  final bool profileComplete;

  /// True when the session ended because the server rejected the tokens.
  final bool expired;

  bool get isSignedIn => status == SessionStatus.signedIn;

  @override
  bool operator ==(Object other) =>
      other is SessionState &&
      other.status == status &&
      other.profileComplete == profileComplete &&
      other.expired == expired;

  @override
  int get hashCode => Object.hash(status, profileComplete, expired);

  @override
  String toString() => 'SessionState(${status.name}, complete: $profileComplete)';
}
