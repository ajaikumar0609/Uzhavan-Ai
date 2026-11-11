import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_ta.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'generated/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('ta'),
  ];

  /// No description provided for @appTitle.
  ///
  /// In ta, this message translates to:
  /// **'UZHAVAN AI'**
  String get appTitle;

  /// No description provided for @languageSwitchLabel.
  ///
  /// In ta, this message translates to:
  /// **'தமிழ் → English'**
  String get languageSwitchLabel;

  /// No description provided for @languageSwitchTooltip.
  ///
  /// In ta, this message translates to:
  /// **'மொழியை மாற்று'**
  String get languageSwitchTooltip;

  /// No description provided for @languageTamil.
  ///
  /// In ta, this message translates to:
  /// **'தமிழ்'**
  String get languageTamil;

  /// No description provided for @languageEnglish.
  ///
  /// In ta, this message translates to:
  /// **'English'**
  String get languageEnglish;

  /// No description provided for @notSet.
  ///
  /// In ta, this message translates to:
  /// **'அமைக்கப்படவில்லை'**
  String get notSet;

  /// No description provided for @optionalSuffix.
  ///
  /// In ta, this message translates to:
  /// **'(விருப்பம்)'**
  String get optionalSuffix;

  /// No description provided for @retry.
  ///
  /// In ta, this message translates to:
  /// **'மீண்டும் முயற்சி'**
  String get retry;

  /// No description provided for @loading.
  ///
  /// In ta, this message translates to:
  /// **'ஏற்றுகிறது…'**
  String get loading;

  /// No description provided for @stateError.
  ///
  /// In ta, this message translates to:
  /// **'ஏதோ தவறு நடந்தது'**
  String get stateError;

  /// No description provided for @stateUnsure.
  ///
  /// In ta, this message translates to:
  /// **'உறுதியாகச் சொல்ல முடியவில்லை: வேளாண் அலுவலரை அணுகவும்'**
  String get stateUnsure;

  /// No description provided for @stateUnavailable.
  ///
  /// In ta, this message translates to:
  /// **'இந்தச் சேவை தற்போது கிடைக்கவில்லை'**
  String get stateUnavailable;

  /// No description provided for @stateEmpty.
  ///
  /// In ta, this message translates to:
  /// **'காட்ட எதுவும் இல்லை'**
  String get stateEmpty;

  /// No description provided for @comingSoon.
  ///
  /// In ta, this message translates to:
  /// **'இந்த வசதி அடுத்த புதுப்பிப்பில் வரும்'**
  String get comingSoon;

  /// No description provided for @navHome.
  ///
  /// In ta, this message translates to:
  /// **'முகப்பு'**
  String get navHome;

  /// No description provided for @navAssistant.
  ///
  /// In ta, this message translates to:
  /// **'உதவி'**
  String get navAssistant;

  /// No description provided for @navScan.
  ///
  /// In ta, this message translates to:
  /// **'ஸ்கேன்'**
  String get navScan;

  /// No description provided for @navMarket.
  ///
  /// In ta, this message translates to:
  /// **'சந்தை'**
  String get navMarket;

  /// No description provided for @navMore.
  ///
  /// In ta, this message translates to:
  /// **'மேலும்'**
  String get navMore;

  /// No description provided for @featureHome.
  ///
  /// In ta, this message translates to:
  /// **'முகப்பு'**
  String get featureHome;

  /// No description provided for @featureAssistant.
  ///
  /// In ta, this message translates to:
  /// **'வேளாண் உதவியாளர்'**
  String get featureAssistant;

  /// No description provided for @featureScan.
  ///
  /// In ta, this message translates to:
  /// **'பயிர் நோய் ஸ்கேன்'**
  String get featureScan;

  /// No description provided for @featureMarket.
  ///
  /// In ta, this message translates to:
  /// **'சந்தை விலைகள்'**
  String get featureMarket;

  /// No description provided for @featureWeather.
  ///
  /// In ta, this message translates to:
  /// **'வானிலை'**
  String get featureWeather;

  /// No description provided for @featureSchemes.
  ///
  /// In ta, this message translates to:
  /// **'அரசு திட்டங்கள்'**
  String get featureSchemes;

  /// No description provided for @featureSoil.
  ///
  /// In ta, this message translates to:
  /// **'மண்'**
  String get featureSoil;

  /// No description provided for @featureFarms.
  ///
  /// In ta, this message translates to:
  /// **'என் பண்ணைகள்'**
  String get featureFarms;

  /// No description provided for @featureDiary.
  ///
  /// In ta, this message translates to:
  /// **'பண்ணை நாட்குறிப்பு'**
  String get featureDiary;

  /// No description provided for @featureSatellite.
  ///
  /// In ta, this message translates to:
  /// **'செயற்கைக்கோள்'**
  String get featureSatellite;

  /// No description provided for @featureProfile.
  ///
  /// In ta, this message translates to:
  /// **'சுயவிவரம்'**
  String get featureProfile;

  /// No description provided for @featureSettings.
  ///
  /// In ta, this message translates to:
  /// **'அமைப்புகள்'**
  String get featureSettings;

  /// No description provided for @back.
  ///
  /// In ta, this message translates to:
  /// **'பின்செல்'**
  String get back;

  /// No description provided for @loginTitle.
  ///
  /// In ta, this message translates to:
  /// **'உள்நுழைக'**
  String get loginTitle;

  /// No description provided for @loginSubtitle.
  ///
  /// In ta, this message translates to:
  /// **'உங்கள் தொலைபேசி எண்ணை உள்ளிடுங்கள்'**
  String get loginSubtitle;

  /// No description provided for @phoneLabel.
  ///
  /// In ta, this message translates to:
  /// **'தொலைபேசி எண்'**
  String get phoneLabel;

  /// No description provided for @phonePrefix.
  ///
  /// In ta, this message translates to:
  /// **'+91'**
  String get phonePrefix;

  /// No description provided for @phoneHint.
  ///
  /// In ta, this message translates to:
  /// **'10 இலக்க எண்'**
  String get phoneHint;

  /// No description provided for @phoneInvalid.
  ///
  /// In ta, this message translates to:
  /// **'6, 7, 8 அல்லது 9 இல் தொடங்கும் 10 இலக்க எண்ணை உள்ளிடுங்கள்'**
  String get phoneInvalid;

  /// No description provided for @sendOtp.
  ///
  /// In ta, this message translates to:
  /// **'OTP அனுப்பு'**
  String get sendOtp;

  /// No description provided for @otpTitle.
  ///
  /// In ta, this message translates to:
  /// **'தொலைபேசி சரிபார்ப்பு'**
  String get otpTitle;

  /// No description provided for @otpSentTo.
  ///
  /// In ta, this message translates to:
  /// **'+91 {phone} க்கு OTP அனுப்பப்பட்டது'**
  String otpSentTo(String phone);

  /// No description provided for @otpLabel.
  ///
  /// In ta, this message translates to:
  /// **'6 இலக்க OTP'**
  String get otpLabel;

  /// No description provided for @otpInvalid.
  ///
  /// In ta, this message translates to:
  /// **'6 இலக்கக் குறியீட்டை உள்ளிடுங்கள்'**
  String get otpInvalid;

  /// No description provided for @verify.
  ///
  /// In ta, this message translates to:
  /// **'சரிபார்'**
  String get verify;

  /// No description provided for @resendOtp.
  ///
  /// In ta, this message translates to:
  /// **'குறியீட்டை மீண்டும் அனுப்பு'**
  String get resendOtp;

  /// No description provided for @resendIn.
  ///
  /// In ta, this message translates to:
  /// **'{seconds} வினாடிகளில் மீண்டும் அனுப்பலாம்'**
  String resendIn(int seconds);

  /// No description provided for @changeNumber.
  ///
  /// In ta, this message translates to:
  /// **'எண்ணை மாற்று'**
  String get changeNumber;

  /// No description provided for @otpResent.
  ///
  /// In ta, this message translates to:
  /// **'புதிய குறியீடு அனுப்பப்பட்டது'**
  String get otpResent;

  /// No description provided for @errOtpIncorrect.
  ///
  /// In ta, this message translates to:
  /// **'தவறான குறியீடு. மீண்டும் முயற்சிக்கவும்.'**
  String get errOtpIncorrect;

  /// No description provided for @errOtpExpired.
  ///
  /// In ta, this message translates to:
  /// **'குறியீடு காலாவதியானது. புதிய குறியீட்டைக் கோருங்கள்.'**
  String get errOtpExpired;

  /// No description provided for @errOtpAttemptsExceeded.
  ///
  /// In ta, this message translates to:
  /// **'பல தவறான முயற்சிகள். புதிய குறியீட்டைக் கோருங்கள்.'**
  String get errOtpAttemptsExceeded;

  /// No description provided for @errOtpNotFound.
  ///
  /// In ta, this message translates to:
  /// **'செயலில் உள்ள குறியீடு இல்லை. புதிய குறியீட்டைக் கோருங்கள்.'**
  String get errOtpNotFound;

  /// No description provided for @errRateLimited.
  ///
  /// In ta, this message translates to:
  /// **'பல கோரிக்கைகள். சிறிது நேரம் கழித்து முயற்சிக்கவும்.'**
  String get errRateLimited;

  /// No description provided for @errRateLimitedSeconds.
  ///
  /// In ta, this message translates to:
  /// **'பல கோரிக்கைகள். {seconds} வினாடிகளில் மீண்டும் முயற்சிக்கவும்.'**
  String errRateLimitedSeconds(int seconds);

  /// No description provided for @errRateLimitedMinutes.
  ///
  /// In ta, this message translates to:
  /// **'பல கோரிக்கைகள். {minutes} நிமிடங்களில் மீண்டும் முயற்சிக்கவும்.'**
  String errRateLimitedMinutes(int minutes);

  /// No description provided for @errOtpDeliveryNotConfigured.
  ///
  /// In ta, this message translates to:
  /// **'SMS சேவை தற்போது கிடைக்கவில்லை. பின்னர் முயற்சிக்கவும்.'**
  String get errOtpDeliveryNotConfigured;

  /// No description provided for @errServerUnreachable.
  ///
  /// In ta, this message translates to:
  /// **'UZHAVAN சேவையகத்தை அணுக முடியவில்லை'**
  String get errServerUnreachable;

  /// No description provided for @errSessionExpired.
  ///
  /// In ta, this message translates to:
  /// **'உங்கள் அமர்வு முடிந்தது. மீண்டும் உள்நுழையவும்.'**
  String get errSessionExpired;

  /// No description provided for @errValidation.
  ///
  /// In ta, this message translates to:
  /// **'உள்ளிட்ட விவரங்களைச் சரிபார்க்கவும்'**
  String get errValidation;

  /// No description provided for @errNotFound.
  ///
  /// In ta, this message translates to:
  /// **'கோரிய தகவல் கிடைக்கவில்லை'**
  String get errNotFound;

  /// No description provided for @profileName.
  ///
  /// In ta, this message translates to:
  /// **'பெயர்'**
  String get profileName;

  /// No description provided for @profileDistrict.
  ///
  /// In ta, this message translates to:
  /// **'மாவட்டம்'**
  String get profileDistrict;

  /// No description provided for @profileVillage.
  ///
  /// In ta, this message translates to:
  /// **'கிராமம்'**
  String get profileVillage;

  /// No description provided for @profilePhone.
  ///
  /// In ta, this message translates to:
  /// **'தொலைபேசி'**
  String get profilePhone;

  /// No description provided for @profileLanguage.
  ///
  /// In ta, this message translates to:
  /// **'விருப்ப மொழி'**
  String get profileLanguage;

  /// No description provided for @profileEdit.
  ///
  /// In ta, this message translates to:
  /// **'சுயவிவரத்தைத் திருத்து'**
  String get profileEdit;

  /// No description provided for @profileUnavailable.
  ///
  /// In ta, this message translates to:
  /// **'சுயவிவரத் தரவு கிடைக்கவில்லை'**
  String get profileUnavailable;

  /// No description provided for @profileStillIncomplete.
  ///
  /// In ta, this message translates to:
  /// **'சுயவிவரம் இன்னும் முழுமையடையவில்லை. தேவையான விவரங்களை நிரப்பவும்.'**
  String get profileStillIncomplete;

  /// No description provided for @onboardingTitle.
  ///
  /// In ta, this message translates to:
  /// **'உங்கள் விவரங்கள்'**
  String get onboardingTitle;

  /// No description provided for @onboardingSubtitle.
  ///
  /// In ta, this message translates to:
  /// **'சிறந்த ஆலோசனைக்கு உதவும்'**
  String get onboardingSubtitle;

  /// No description provided for @onboardingContinue.
  ///
  /// In ta, this message translates to:
  /// **'தொடரவும்'**
  String get onboardingContinue;

  /// No description provided for @nameInvalid.
  ///
  /// In ta, this message translates to:
  /// **'பெயர் 2 முதல் 100 எழுத்துகள் இருக்க வேண்டும்'**
  String get nameInvalid;

  /// No description provided for @districtRequired.
  ///
  /// In ta, this message translates to:
  /// **'மாவட்டத்தைத் தேர்ந்தெடுக்கவும்'**
  String get districtRequired;

  /// No description provided for @districtPickerTitle.
  ///
  /// In ta, this message translates to:
  /// **'மாவட்டத்தைத் தேர்ந்தெடுக்கவும்'**
  String get districtPickerTitle;

  /// No description provided for @searchHint.
  ///
  /// In ta, this message translates to:
  /// **'தேடு'**
  String get searchHint;

  /// No description provided for @districtsUnavailable.
  ///
  /// In ta, this message translates to:
  /// **'மாவட்டப் பட்டியல் கிடைக்கவில்லை'**
  String get districtsUnavailable;

  /// No description provided for @optionsUnavailable.
  ///
  /// In ta, this message translates to:
  /// **'தேர்வுப் பட்டியல் கிடைக்கவில்லை'**
  String get optionsUnavailable;

  /// No description provided for @noMatches.
  ///
  /// In ta, this message translates to:
  /// **'பொருத்தம் எதுவும் இல்லை'**
  String get noMatches;

  /// No description provided for @pickerNone.
  ///
  /// In ta, this message translates to:
  /// **'தேர்வு செய்யவில்லை'**
  String get pickerNone;

  /// No description provided for @save.
  ///
  /// In ta, this message translates to:
  /// **'சேமி'**
  String get save;

  /// No description provided for @cancel.
  ///
  /// In ta, this message translates to:
  /// **'ரத்து செய்'**
  String get cancel;

  /// No description provided for @saved.
  ///
  /// In ta, this message translates to:
  /// **'சேமிக்கப்பட்டது'**
  String get saved;

  /// No description provided for @delete.
  ///
  /// In ta, this message translates to:
  /// **'நீக்கு'**
  String get delete;

  /// No description provided for @edit.
  ///
  /// In ta, this message translates to:
  /// **'திருத்து'**
  String get edit;

  /// No description provided for @logout.
  ///
  /// In ta, this message translates to:
  /// **'வெளியேறு'**
  String get logout;

  /// No description provided for @logoutConfirm.
  ///
  /// In ta, this message translates to:
  /// **'UZHAVAN AI இலிருந்து வெளியேற வேண்டுமா?'**
  String get logoutConfirm;

  /// No description provided for @farmAdd.
  ///
  /// In ta, this message translates to:
  /// **'பண்ணையைச் சேர்'**
  String get farmAdd;

  /// No description provided for @farmEdit.
  ///
  /// In ta, this message translates to:
  /// **'பண்ணையைத் திருத்து'**
  String get farmEdit;

  /// No description provided for @farmDeleteConfirm.
  ///
  /// In ta, this message translates to:
  /// **'\"{name}\" பண்ணையை நீக்க வேண்டுமா?'**
  String farmDeleteConfirm(String name);

  /// No description provided for @farmDeleted.
  ///
  /// In ta, this message translates to:
  /// **'பண்ணை நீக்கப்பட்டது'**
  String get farmDeleted;

  /// No description provided for @farmsEmpty.
  ///
  /// In ta, this message translates to:
  /// **'இன்னும் பண்ணைகள் சேர்க்கப்படவில்லை'**
  String get farmsEmpty;

  /// No description provided for @farmsUnavailable.
  ///
  /// In ta, this message translates to:
  /// **'பண்ணை தரவு கிடைக்கவில்லை'**
  String get farmsUnavailable;

  /// No description provided for @farmName.
  ///
  /// In ta, this message translates to:
  /// **'பண்ணையின் பெயர்'**
  String get farmName;

  /// No description provided for @farmNameRequired.
  ///
  /// In ta, this message translates to:
  /// **'பண்ணையின் பெயரை உள்ளிடுங்கள்'**
  String get farmNameRequired;

  /// No description provided for @farmLocation.
  ///
  /// In ta, this message translates to:
  /// **'இருப்பிடம்'**
  String get farmLocation;

  /// No description provided for @farmLocationHelp.
  ///
  /// In ta, this message translates to:
  /// **'அட்சரேகை, தீர்க்கரேகை இரண்டையும் உள்ளிடுங்கள் அல்லது இரண்டையும் காலியாக விடுங்கள்'**
  String get farmLocationHelp;

  /// No description provided for @farmLatitude.
  ///
  /// In ta, this message translates to:
  /// **'அட்சரேகை'**
  String get farmLatitude;

  /// No description provided for @farmLongitude.
  ///
  /// In ta, this message translates to:
  /// **'தீர்க்கரேகை'**
  String get farmLongitude;

  /// No description provided for @farmLatInvalid.
  ///
  /// In ta, this message translates to:
  /// **'அட்சரேகை 8.0 முதல் 13.6 வரை இருக்க வேண்டும் (தமிழ்நாடு)'**
  String get farmLatInvalid;

  /// No description provided for @farmLonInvalid.
  ///
  /// In ta, this message translates to:
  /// **'தீர்க்கரேகை 76.2 முதல் 80.4 வரை இருக்க வேண்டும் (தமிழ்நாடு)'**
  String get farmLonInvalid;

  /// No description provided for @farmLatLonPair.
  ///
  /// In ta, this message translates to:
  /// **'அட்சரேகை, தீர்க்கரேகை இரண்டும் தேவை'**
  String get farmLatLonPair;

  /// No description provided for @farmCoordinatesValue.
  ///
  /// In ta, this message translates to:
  /// **'{lat}, {lon}'**
  String farmCoordinatesValue(String lat, String lon);

  /// No description provided for @farmArea.
  ///
  /// In ta, this message translates to:
  /// **'நில அளவு (ஏக்கர்)'**
  String get farmArea;

  /// No description provided for @farmAreaInvalid.
  ///
  /// In ta, this message translates to:
  /// **'சரியான ஏக்கர் அளவை உள்ளிடுங்கள்'**
  String get farmAreaInvalid;

  /// No description provided for @farmAreaValue.
  ///
  /// In ta, this message translates to:
  /// **'{acres} ஏக்கர்'**
  String farmAreaValue(String acres);

  /// No description provided for @farmCrop.
  ///
  /// In ta, this message translates to:
  /// **'பயிர்'**
  String get farmCrop;

  /// No description provided for @farmStage.
  ///
  /// In ta, this message translates to:
  /// **'பயிர் நிலை'**
  String get farmStage;

  /// No description provided for @farmSeason.
  ///
  /// In ta, this message translates to:
  /// **'பருவம்'**
  String get farmSeason;

  /// No description provided for @farmIrrigation.
  ///
  /// In ta, this message translates to:
  /// **'பாசன வகை'**
  String get farmIrrigation;

  /// No description provided for @settingsLanguage.
  ///
  /// In ta, this message translates to:
  /// **'மொழி'**
  String get settingsLanguage;

  /// No description provided for @settingsTheme.
  ///
  /// In ta, this message translates to:
  /// **'தீம்'**
  String get settingsTheme;

  /// No description provided for @themeLight.
  ///
  /// In ta, this message translates to:
  /// **'வெளிச்சம்'**
  String get themeLight;

  /// No description provided for @themeDark.
  ///
  /// In ta, this message translates to:
  /// **'இருள்'**
  String get themeDark;

  /// No description provided for @themeSystem.
  ///
  /// In ta, this message translates to:
  /// **'சாதன அமைப்பு'**
  String get themeSystem;

  /// No description provided for @settingsAbout.
  ///
  /// In ta, this message translates to:
  /// **'பயன்பாட்டைப் பற்றி'**
  String get settingsAbout;

  /// No description provided for @aboutDescription.
  ///
  /// In ta, this message translates to:
  /// **'தமிழ்நாடு விவசாயிகளுக்கான வேளாண் உதவியாளர்'**
  String get aboutDescription;

  /// No description provided for @appVersion.
  ///
  /// In ta, this message translates to:
  /// **'பதிப்பு {version}'**
  String appVersion(String version);

  /// No description provided for @apiBaseUrlDebug.
  ///
  /// In ta, this message translates to:
  /// **'API முகவரி (டீபக்): {url}'**
  String apiBaseUrlDebug(String url);

  /// No description provided for @configErrorTitle.
  ///
  /// In ta, this message translates to:
  /// **'அமைப்புப் பிழை'**
  String get configErrorTitle;

  /// No description provided for @configErrorInsecure.
  ///
  /// In ta, this message translates to:
  /// **'இந்த வெளியீட்டுப் பதிப்புக்கு பாதுகாப்பான (https) API முகவரி தேவை.'**
  String get configErrorInsecure;

  /// No description provided for @configErrorInvalid.
  ///
  /// In ta, this message translates to:
  /// **'API முகவரி தவறானது.'**
  String get configErrorInvalid;

  /// No description provided for @configErrorDetail.
  ///
  /// In ta, this message translates to:
  /// **'API_BASE_URL: {url}'**
  String configErrorDetail(String url);

  /// No description provided for @farmLimitReached.
  ///
  /// In ta, this message translates to:
  /// **'அதிகபட்சம் 5 பண்ணைகள் மட்டுமே சேர்க்கலாம்'**
  String get farmLimitReached;

  /// No description provided for @errInvalidDistrict.
  ///
  /// In ta, this message translates to:
  /// **'தேர்ந்தெடுத்த மாவட்டம் சரியானதல்ல'**
  String get errInvalidDistrict;

  /// No description provided for @errInvalidLanguage.
  ///
  /// In ta, this message translates to:
  /// **'தேர்ந்தெடுத்த மொழி சரியானதல்ல'**
  String get errInvalidLanguage;

  /// No description provided for @errInvalidVillage.
  ///
  /// In ta, this message translates to:
  /// **'கிராமத்தின் பெயரைச் சரிபார்க்கவும்'**
  String get errInvalidVillage;

  /// No description provided for @errInvalidLocation.
  ///
  /// In ta, this message translates to:
  /// **'இருப்பிட மதிப்புகள் சரியானவை அல்ல'**
  String get errInvalidLocation;

  /// No description provided for @errLocationOutsideTn.
  ///
  /// In ta, this message translates to:
  /// **'இருப்பிடம் தமிழ்நாட்டுக்குள் இருக்க வேண்டும்'**
  String get errLocationOutsideTn;

  /// No description provided for @errInvalidBoundary.
  ///
  /// In ta, this message translates to:
  /// **'பண்ணை எல்லை சரியானதல்ல'**
  String get errInvalidBoundary;

  /// No description provided for @errInvalidCrop.
  ///
  /// In ta, this message translates to:
  /// **'தேர்ந்தெடுத்த பயிர் சரியானதல்ல'**
  String get errInvalidCrop;

  /// No description provided for @errInvalidCropStage.
  ///
  /// In ta, this message translates to:
  /// **'தேர்ந்தெடுத்த பயிர் நிலை சரியானதல்ல'**
  String get errInvalidCropStage;

  /// No description provided for @errInvalidSeason.
  ///
  /// In ta, this message translates to:
  /// **'தேர்ந்தெடுத்த பருவம் சரியானதல்ல'**
  String get errInvalidSeason;

  /// No description provided for @errInvalidIrrigationType.
  ///
  /// In ta, this message translates to:
  /// **'தேர்ந்தெடுத்த பாசன வகை சரியானதல்ல'**
  String get errInvalidIrrigationType;

  /// No description provided for @notAvailable.
  ///
  /// In ta, this message translates to:
  /// **'கிடைக்கவில்லை'**
  String get notAvailable;

  /// No description provided for @sourceLabel.
  ///
  /// In ta, this message translates to:
  /// **'ஆதாரம்: {source}'**
  String sourceLabel(String source);

  /// No description provided for @updatedAt.
  ///
  /// In ta, this message translates to:
  /// **'புதுப்பித்தது {time}'**
  String updatedAt(String time);

  /// No description provided for @observedOn.
  ///
  /// In ta, this message translates to:
  /// **'பதிவான நாள் {date}'**
  String observedOn(String date);

  /// No description provided for @oldData.
  ///
  /// In ta, this message translates to:
  /// **'பழைய தரவு'**
  String get oldData;

  /// No description provided for @kindCurrent.
  ///
  /// In ta, this message translates to:
  /// **'தற்போது'**
  String get kindCurrent;

  /// No description provided for @kindForecast.
  ///
  /// In ta, this message translates to:
  /// **'முன்னறிவிப்பு'**
  String get kindForecast;

  /// No description provided for @kindHistorical.
  ///
  /// In ta, this message translates to:
  /// **'கடந்த கால தரவு'**
  String get kindHistorical;

  /// No description provided for @kindLatestObserved.
  ///
  /// In ta, this message translates to:
  /// **'சமீபத்திய பதிவு'**
  String get kindLatestObserved;

  /// No description provided for @kindEstimated.
  ///
  /// In ta, this message translates to:
  /// **'மாதிரி மதிப்பீடு'**
  String get kindEstimated;

  /// No description provided for @kindMeasured.
  ///
  /// In ta, this message translates to:
  /// **'அளவிடப்பட்டது'**
  String get kindMeasured;

  /// No description provided for @kindReference.
  ///
  /// In ta, this message translates to:
  /// **'குறிப்புத் தகவல்'**
  String get kindReference;

  /// No description provided for @linkOpenFailed.
  ///
  /// In ta, this message translates to:
  /// **'இணைப்பைத் திறக்க முடியவில்லை'**
  String get linkOpenFailed;

  /// No description provided for @farmPickerLabel.
  ///
  /// In ta, this message translates to:
  /// **'பண்ணை'**
  String get farmPickerLabel;

  /// No description provided for @locationMissing.
  ///
  /// In ta, this message translates to:
  /// **'பண்ணையைச் சேர்க்கவும் அல்லது சுயவிவரத்தில் மாவட்டத்தை அமைக்கவும்'**
  String get locationMissing;

  /// No description provided for @close.
  ///
  /// In ta, this message translates to:
  /// **'மூடு'**
  String get close;

  /// No description provided for @weatherUnavailable.
  ///
  /// In ta, this message translates to:
  /// **'வானிலை தரவு தற்போது கிடைக்கவில்லை'**
  String get weatherUnavailable;

  /// No description provided for @weatherNow.
  ///
  /// In ta, this message translates to:
  /// **'தற்போதைய வானிலை'**
  String get weatherNow;

  /// No description provided for @weatherLocation.
  ///
  /// In ta, this message translates to:
  /// **'இடம்: {name}'**
  String weatherLocation(String name);

  /// No description provided for @weatherFeelsLike.
  ///
  /// In ta, this message translates to:
  /// **'உணரும் வெப்பம்'**
  String get weatherFeelsLike;

  /// No description provided for @weatherHumidity.
  ///
  /// In ta, this message translates to:
  /// **'ஈரப்பதம்'**
  String get weatherHumidity;

  /// No description provided for @weatherRain.
  ///
  /// In ta, this message translates to:
  /// **'மழை'**
  String get weatherRain;

  /// No description provided for @weatherWind.
  ///
  /// In ta, this message translates to:
  /// **'காற்று'**
  String get weatherWind;

  /// No description provided for @weatherModelTime.
  ///
  /// In ta, this message translates to:
  /// **'மாதிரி நேரம்'**
  String get weatherModelTime;

  /// No description provided for @weatherForecast7.
  ///
  /// In ta, this message translates to:
  /// **'7 நாள் முன்னறிவிப்பு'**
  String get weatherForecast7;

  /// No description provided for @weatherToday.
  ///
  /// In ta, this message translates to:
  /// **'இன்றைய முன்னறிவிப்பு'**
  String get weatherToday;

  /// No description provided for @weatherForecastEmpty.
  ///
  /// In ta, this message translates to:
  /// **'முன்னறிவிப்பு தரவு இல்லை'**
  String get weatherForecastEmpty;

  /// No description provided for @weatherMaxMin.
  ///
  /// In ta, this message translates to:
  /// **'அதிகம் {max} · குறைவு {min}'**
  String weatherMaxMin(String max, String min);

  /// No description provided for @weatherRainLine.
  ///
  /// In ta, this message translates to:
  /// **'மழை {mm} · வாய்ப்பு {pct}'**
  String weatherRainLine(String mm, String pct);

  /// No description provided for @weatherAdvisories.
  ///
  /// In ta, this message translates to:
  /// **'வானிலை அறிவுரைகள்'**
  String get weatherAdvisories;

  /// No description provided for @weatherNoAdvisories.
  ///
  /// In ta, this message translates to:
  /// **'தற்போது எந்த விதியும் பொருந்தவில்லை'**
  String get weatherNoAdvisories;

  /// No description provided for @severityCaution.
  ///
  /// In ta, this message translates to:
  /// **'எச்சரிக்கை'**
  String get severityCaution;

  /// No description provided for @severityInfo.
  ///
  /// In ta, this message translates to:
  /// **'தகவல்'**
  String get severityInfo;

  /// No description provided for @ruleSource.
  ///
  /// In ta, this message translates to:
  /// **'விதியின் ஆதாரம்: {source}'**
  String ruleSource(String source);

  /// No description provided for @marketUnavailable.
  ///
  /// In ta, this message translates to:
  /// **'சந்தை தரவு தற்போது கிடைக்கவில்லை'**
  String get marketUnavailable;

  /// No description provided for @marketEmpty.
  ///
  /// In ta, this message translates to:
  /// **'இந்தத் தேர்வுக்கு விலைப் பதிவுகள் இல்லை'**
  String get marketEmpty;

  /// No description provided for @marketDistrictFilter.
  ///
  /// In ta, this message translates to:
  /// **'மாவட்டம்'**
  String get marketDistrictFilter;

  /// No description provided for @allCommodities.
  ///
  /// In ta, this message translates to:
  /// **'அனைத்தும்'**
  String get allCommodities;

  /// No description provided for @marketLatestTitle.
  ///
  /// In ta, this message translates to:
  /// **'சமீபத்திய விலைப் பதிவுகள்'**
  String get marketLatestTitle;

  /// No description provided for @marketTapForTrend.
  ///
  /// In ta, this message translates to:
  /// **'கடந்த கால விலைப் போக்கைப் பார்க்க ஒரு பதிவைத் தொடவும்'**
  String get marketTapForTrend;

  /// No description provided for @marketMinMax.
  ///
  /// In ta, this message translates to:
  /// **'குறைந்தது ₹ {min} – அதிகம் ₹ {max}'**
  String marketMinMax(String min, String max);

  /// No description provided for @unitRsPerQuintal.
  ///
  /// In ta, this message translates to:
  /// **'ரூ/குவிண்டால்'**
  String get unitRsPerQuintal;

  /// No description provided for @unitNoteLabel.
  ///
  /// In ta, this message translates to:
  /// **'அலகுக் குறிப்பு: {note}'**
  String unitNoteLabel(String note);

  /// No description provided for @marketTrend.
  ///
  /// In ta, this message translates to:
  /// **'விலைப் போக்கு (கடந்த காலம்)'**
  String get marketTrend;

  /// No description provided for @marketTrendTitle.
  ///
  /// In ta, this message translates to:
  /// **'{name}: கடந்த கால விலைப் போக்கு'**
  String marketTrendTitle(String name);

  /// No description provided for @marketTrendCaption.
  ///
  /// In ta, this message translates to:
  /// **'{market} · கடந்த {days} நாட்கள் · பொதுவான (modal) விலை'**
  String marketTrendCaption(String market, int days);

  /// No description provided for @marketTrendEmpty.
  ///
  /// In ta, this message translates to:
  /// **'இந்தச் சந்தைக்குக் கடந்த கால விலைகள் இல்லை'**
  String get marketTrendEmpty;

  /// No description provided for @schemesUnavailable.
  ///
  /// In ta, this message translates to:
  /// **'திட்டத் தரவு தற்போது கிடைக்கவில்லை'**
  String get schemesUnavailable;

  /// No description provided for @schemesEmpty.
  ///
  /// In ta, this message translates to:
  /// **'இந்தத் தேடலுக்குத் திட்டங்கள் இல்லை'**
  String get schemesEmpty;

  /// No description provided for @schemeSearchHint.
  ///
  /// In ta, this message translates to:
  /// **'திட்டங்களைத் தேடுங்கள்'**
  String get schemeSearchHint;

  /// No description provided for @levelAll.
  ///
  /// In ta, this message translates to:
  /// **'அனைத்தும்'**
  String get levelAll;

  /// No description provided for @levelCentral.
  ///
  /// In ta, this message translates to:
  /// **'மத்திய அரசு'**
  String get levelCentral;

  /// No description provided for @levelState.
  ///
  /// In ta, this message translates to:
  /// **'மாநில அரசு'**
  String get levelState;

  /// No description provided for @schemeCropFilter.
  ///
  /// In ta, this message translates to:
  /// **'பயிர்'**
  String get schemeCropFilter;

  /// No description provided for @schemesCount.
  ///
  /// In ta, this message translates to:
  /// **'{count} திட்டங்கள்'**
  String schemesCount(int count);

  /// No description provided for @schemeInactive.
  ///
  /// In ta, this message translates to:
  /// **'மூலத்தில் செயலில் இல்லை'**
  String get schemeInactive;

  /// No description provided for @schemeLevel.
  ///
  /// In ta, this message translates to:
  /// **'நிலை'**
  String get schemeLevel;

  /// No description provided for @schemeAuthority.
  ///
  /// In ta, this message translates to:
  /// **'பொறுப்பு அமைப்பு'**
  String get schemeAuthority;

  /// No description provided for @schemeDateChecked.
  ///
  /// In ta, this message translates to:
  /// **'சரிபார்த்த நாள்'**
  String get schemeDateChecked;

  /// No description provided for @schemeLastUpdatedOnSource.
  ///
  /// In ta, this message translates to:
  /// **'மூலத்தில் புதுப்பித்த நாள்'**
  String get schemeLastUpdatedOnSource;

  /// No description provided for @schemeOfficialLink.
  ///
  /// In ta, this message translates to:
  /// **'அதிகாரப்பூர்வ இணையப் பக்கம்'**
  String get schemeOfficialLink;

  /// No description provided for @schemeDescription.
  ///
  /// In ta, this message translates to:
  /// **'விளக்கம்'**
  String get schemeDescription;

  /// No description provided for @schemeEligibilityText.
  ///
  /// In ta, this message translates to:
  /// **'தகுதி விவரம் (அதிகாரப்பூர்வ உரை)'**
  String get schemeEligibilityText;

  /// No description provided for @schemeBenefits.
  ///
  /// In ta, this message translates to:
  /// **'பயன்கள்'**
  String get schemeBenefits;

  /// No description provided for @schemeHowToApply.
  ///
  /// In ta, this message translates to:
  /// **'விண்ணப்பிக்கும் முறை'**
  String get schemeHowToApply;

  /// No description provided for @schemeDocuments.
  ///
  /// In ta, this message translates to:
  /// **'தேவையான ஆவணங்கள்'**
  String get schemeDocuments;

  /// No description provided for @schemeSourceDocuments.
  ///
  /// In ta, this message translates to:
  /// **'மூல ஆவணங்கள்'**
  String get schemeSourceDocuments;

  /// No description provided for @eligibilityTitle.
  ///
  /// In ta, this message translates to:
  /// **'உங்கள் தகுதி சரிபார்ப்பு'**
  String get eligibilityTitle;

  /// No description provided for @eligibilityUnavailable.
  ///
  /// In ta, this message translates to:
  /// **'தகுதி சரிபார்ப்பு தற்போது கிடைக்கவில்லை'**
  String get eligibilityUnavailable;

  /// No description provided for @eligMeetsKnown.
  ///
  /// In ta, this message translates to:
  /// **'அறியப்பட்ட நிபந்தனைகளைப் பூர்த்தி செய்கிறீர்கள்'**
  String get eligMeetsKnown;

  /// No description provided for @eligFailsKnown.
  ///
  /// In ta, this message translates to:
  /// **'அறியப்பட்ட நிபந்தனைகளைப் பூர்த்தி செய்யவில்லை'**
  String get eligFailsKnown;

  /// No description provided for @eligMoreInfo.
  ///
  /// In ta, this message translates to:
  /// **'மேலும் தகவல் தேவை'**
  String get eligMoreInfo;

  /// No description provided for @eligCannotDetermine.
  ///
  /// In ta, this message translates to:
  /// **'தீர்மானிக்க முடியவில்லை'**
  String get eligCannotDetermine;

  /// No description provided for @eligibilityNoResult.
  ///
  /// In ta, this message translates to:
  /// **'தகுதி முடிவு கிடைக்கவில்லை'**
  String get eligibilityNoResult;

  /// No description provided for @eligibilityReasons.
  ///
  /// In ta, this message translates to:
  /// **'காரணங்கள்'**
  String get eligibilityReasons;

  /// No description provided for @eligibilityMissing.
  ///
  /// In ta, this message translates to:
  /// **'தேவைப்படும் விவரங்கள்'**
  String get eligibilityMissing;

  /// No description provided for @eligibilityCriteriaSource.
  ///
  /// In ta, this message translates to:
  /// **'நிபந்தனைகளின் ஆதாரம்'**
  String get eligibilityCriteriaSource;

  /// No description provided for @eligibilityDisclaimer.
  ///
  /// In ta, this message translates to:
  /// **'இது அறியப்பட்ட நிபந்தனைகளை மட்டுமே சரிபார்க்கிறது; இறுதி முடிவு அரசு அலுவலகத்தினுடையது.'**
  String get eligibilityDisclaimer;

  /// No description provided for @soilUnavailable.
  ///
  /// In ta, this message translates to:
  /// **'மண் தரவு தற்போது கிடைக்கவில்லை'**
  String get soilUnavailable;

  /// No description provided for @soilRegionalTitle.
  ///
  /// In ta, this message translates to:
  /// **'பிராந்தியத் தகவல்'**
  String get soilRegionalTitle;

  /// No description provided for @soilTypes.
  ///
  /// In ta, this message translates to:
  /// **'இப்பகுதியின் மண் வகைகள்'**
  String get soilTypes;

  /// No description provided for @soilNutrientStatus.
  ///
  /// In ta, this message translates to:
  /// **'மாவட்ட ஊட்டச்சத்து நிலை'**
  String get soilNutrientStatus;

  /// No description provided for @soilNutrientStatusCaption.
  ///
  /// In ta, this message translates to:
  /// **'ஒவ்வொரு வகையிலும் உள்ள மாதிரிகளின் சதவீதம்'**
  String get soilNutrientStatusCaption;

  /// No description provided for @soilEstimatedTitle.
  ///
  /// In ta, this message translates to:
  /// **'மதிப்பிடப்பட்ட (மாதிரி) மதிப்புகள்'**
  String get soilEstimatedTitle;

  /// No description provided for @soilEstimatedWarning.
  ///
  /// In ta, this message translates to:
  /// **'இவை கணினி மாதிரி (model) மதிப்பீடுகள், உங்கள் நிலத்தின் அளவீடுகள் அல்ல'**
  String get soilEstimatedWarning;

  /// No description provided for @soilDepth.
  ///
  /// In ta, this message translates to:
  /// **'ஆழம்'**
  String get soilDepth;

  /// No description provided for @soilMeasuredTitle.
  ///
  /// In ta, this message translates to:
  /// **'உங்கள் மண் பரிசோதனைகள் (அளவிடப்பட்டவை)'**
  String get soilMeasuredTitle;

  /// No description provided for @soilNoTests.
  ///
  /// In ta, this message translates to:
  /// **'இன்னும் மண் பரிசோதனை முடிவுகள் சேர்க்கப்படவில்லை'**
  String get soilNoTests;

  /// No description provided for @soilAddTest.
  ///
  /// In ta, this message translates to:
  /// **'மண் பரிசோதனை சேர்'**
  String get soilAddTest;

  /// No description provided for @soilAddTestNeedsFarm.
  ///
  /// In ta, this message translates to:
  /// **'மண் பரிசோதனை சேர்க்க முதலில் ஒரு பண்ணையைச் சேர்க்கவும்'**
  String get soilAddTestNeedsFarm;

  /// No description provided for @soilSampleOn.
  ///
  /// In ta, this message translates to:
  /// **'மாதிரி எடுத்த நாள்: {date}'**
  String soilSampleOn(String date);

  /// No description provided for @soilLab.
  ///
  /// In ta, this message translates to:
  /// **'ஆய்வகம்: {lab}'**
  String soilLab(String lab);

  /// No description provided for @soilFarmerEntered.
  ///
  /// In ta, this message translates to:
  /// **'நீங்கள் உள்ளிட்டது'**
  String get soilFarmerEntered;

  /// No description provided for @soilSampleDate.
  ///
  /// In ta, this message translates to:
  /// **'மாதிரி எடுத்த நாள்'**
  String get soilSampleDate;

  /// No description provided for @soilPickDate.
  ///
  /// In ta, this message translates to:
  /// **'நாளைத் தேர்ந்தெடுக்கவும்'**
  String get soilPickDate;

  /// No description provided for @soilLabName.
  ///
  /// In ta, this message translates to:
  /// **'ஆய்வகத்தின் பெயர்'**
  String get soilLabName;

  /// No description provided for @soilValuesHint.
  ///
  /// In ta, this message translates to:
  /// **'உங்கள் மண் பரிசோதனை அட்டையில் உள்ள மதிப்புகளை மட்டும் உள்ளிடவும்; மற்றவற்றைக் காலியாக விடவும்.'**
  String get soilValuesHint;

  /// No description provided for @soilValueInvalid.
  ///
  /// In ta, this message translates to:
  /// **'சரியான எண்ணை உள்ளிடவும்'**
  String get soilValueInvalid;

  /// No description provided for @soilValueRange.
  ///
  /// In ta, this message translates to:
  /// **'அனுமதி: {min} – {max}'**
  String soilValueRange(String min, String max);

  /// No description provided for @soilFarmRequired.
  ///
  /// In ta, this message translates to:
  /// **'பண்ணையைத் தேர்ந்தெடுக்கவும்'**
  String get soilFarmRequired;

  /// No description provided for @soilDateRequired.
  ///
  /// In ta, this message translates to:
  /// **'மாதிரி எடுத்த நாளைத் தேர்ந்தெடுக்கவும்'**
  String get soilDateRequired;

  /// No description provided for @soilAtLeastOne.
  ///
  /// In ta, this message translates to:
  /// **'குறைந்தது ஒரு மதிப்பையாவது உள்ளிடவும்'**
  String get soilAtLeastOne;

  /// No description provided for @soilPh.
  ///
  /// In ta, this message translates to:
  /// **'pH'**
  String get soilPh;

  /// No description provided for @soilSoc.
  ///
  /// In ta, this message translates to:
  /// **'மண் கரிமக் கார்பன்'**
  String get soilSoc;

  /// No description provided for @soilClay.
  ///
  /// In ta, this message translates to:
  /// **'களிமண்'**
  String get soilClay;

  /// No description provided for @soilSand.
  ///
  /// In ta, this message translates to:
  /// **'மணல்'**
  String get soilSand;

  /// No description provided for @soilSilt.
  ///
  /// In ta, this message translates to:
  /// **'வண்டல்'**
  String get soilSilt;

  /// No description provided for @soilCec.
  ///
  /// In ta, this message translates to:
  /// **'நேர்மின் அயனி பரிமாற்றத் திறன் (CEC)'**
  String get soilCec;

  /// No description provided for @soilBdod.
  ///
  /// In ta, this message translates to:
  /// **'மண் அடர்த்தி'**
  String get soilBdod;

  /// No description provided for @soilNitrogenEst.
  ///
  /// In ta, this message translates to:
  /// **'மொத்த நைட்ரஜன்'**
  String get soilNitrogenEst;

  /// No description provided for @soilEc.
  ///
  /// In ta, this message translates to:
  /// **'மின் கடத்துத்திறன் (EC)'**
  String get soilEc;

  /// No description provided for @soilOc.
  ///
  /// In ta, this message translates to:
  /// **'கரிமக் கார்பன் (OC)'**
  String get soilOc;

  /// No description provided for @soilN.
  ///
  /// In ta, this message translates to:
  /// **'தழைச்சத்து (N)'**
  String get soilN;

  /// No description provided for @soilP.
  ///
  /// In ta, this message translates to:
  /// **'மணிச்சத்து (P)'**
  String get soilP;

  /// No description provided for @soilK.
  ///
  /// In ta, this message translates to:
  /// **'சாம்பல்சத்து (K)'**
  String get soilK;

  /// No description provided for @soilS.
  ///
  /// In ta, this message translates to:
  /// **'கந்தகம் (S)'**
  String get soilS;

  /// No description provided for @soilZn.
  ///
  /// In ta, this message translates to:
  /// **'துத்தநாகம் (Zn)'**
  String get soilZn;

  /// No description provided for @soilFe.
  ///
  /// In ta, this message translates to:
  /// **'இரும்பு (Fe)'**
  String get soilFe;

  /// No description provided for @soilCu.
  ///
  /// In ta, this message translates to:
  /// **'தாமிரம் (Cu)'**
  String get soilCu;

  /// No description provided for @soilMn.
  ///
  /// In ta, this message translates to:
  /// **'மாங்கனீசு (Mn)'**
  String get soilMn;

  /// No description provided for @soilB.
  ///
  /// In ta, this message translates to:
  /// **'போரான் (B)'**
  String get soilB;

  /// No description provided for @diaryUnavailable.
  ///
  /// In ta, this message translates to:
  /// **'நாட்குறிப்பு தற்போது கிடைக்கவில்லை'**
  String get diaryUnavailable;

  /// No description provided for @diaryEmpty.
  ///
  /// In ta, this message translates to:
  /// **'இன்னும் பதிவுகள் இல்லை'**
  String get diaryEmpty;

  /// No description provided for @diaryAdd.
  ///
  /// In ta, this message translates to:
  /// **'பதிவு சேர்'**
  String get diaryAdd;

  /// No description provided for @diaryKindNote.
  ///
  /// In ta, this message translates to:
  /// **'குறிப்பு'**
  String get diaryKindNote;

  /// No description provided for @diaryKindObservation.
  ///
  /// In ta, this message translates to:
  /// **'கவனிப்பு'**
  String get diaryKindObservation;

  /// No description provided for @diaryKindExpense.
  ///
  /// In ta, this message translates to:
  /// **'செலவு'**
  String get diaryKindExpense;

  /// No description provided for @diaryKindIncome.
  ///
  /// In ta, this message translates to:
  /// **'வருமானம்'**
  String get diaryKindIncome;

  /// No description provided for @diaryKindQuestion.
  ///
  /// In ta, this message translates to:
  /// **'கேள்வி'**
  String get diaryKindQuestion;

  /// No description provided for @diaryKindScan.
  ///
  /// In ta, this message translates to:
  /// **'ஸ்கேன்'**
  String get diaryKindScan;

  /// No description provided for @diaryHistory.
  ///
  /// In ta, this message translates to:
  /// **'வரலாறு'**
  String get diaryHistory;

  /// No description provided for @diaryText.
  ///
  /// In ta, this message translates to:
  /// **'விவரம்'**
  String get diaryText;

  /// No description provided for @diaryTextRequired.
  ///
  /// In ta, this message translates to:
  /// **'விவரத்தை உள்ளிடவும்'**
  String get diaryTextRequired;

  /// No description provided for @diaryAmount.
  ///
  /// In ta, this message translates to:
  /// **'தொகை (ரூ)'**
  String get diaryAmount;

  /// No description provided for @diaryAmountInvalid.
  ///
  /// In ta, this message translates to:
  /// **'சரியான தொகையை உள்ளிடவும்'**
  String get diaryAmountInvalid;

  /// No description provided for @diaryDate.
  ///
  /// In ta, this message translates to:
  /// **'நாள்'**
  String get diaryDate;

  /// No description provided for @satelliteUnavailable.
  ///
  /// In ta, this message translates to:
  /// **'செயற்கைக்கோள் நிலை தற்போது கிடைக்கவில்லை'**
  String get satelliteUnavailable;

  /// No description provided for @satelliteUnderValidation.
  ///
  /// In ta, this message translates to:
  /// **'செயற்கைக்கோள் நுண்ணறிவு சரிபார்ப்பில் உள்ளது'**
  String get satelliteUnderValidation;

  /// No description provided for @satelliteAvailable.
  ///
  /// In ta, this message translates to:
  /// **'செயற்கைக்கோள் நுண்ணறிவு கிடைக்கிறது'**
  String get satelliteAvailable;

  /// No description provided for @satelliteNoPredictions.
  ///
  /// In ta, this message translates to:
  /// **'அனைத்துச் சரிபார்ப்புகளும் முடியும் வரை படங்களோ கணிப்புகளோ காட்டப்படாது.'**
  String get satelliteNoPredictions;

  /// No description provided for @satelliteGates.
  ///
  /// In ta, this message translates to:
  /// **'சரிபார்ப்பு நிலைகள்'**
  String get satelliteGates;

  /// No description provided for @gateLicence.
  ///
  /// In ta, this message translates to:
  /// **'தரவு உரிமம்'**
  String get gateLicence;

  /// No description provided for @gateUnits.
  ///
  /// In ta, this message translates to:
  /// **'அலகுகள் சரிபார்ப்பு'**
  String get gateUnits;

  /// No description provided for @gateGeography.
  ///
  /// In ta, this message translates to:
  /// **'புவியியல் வரம்பு'**
  String get gateGeography;

  /// No description provided for @gateEvaluation.
  ///
  /// In ta, this message translates to:
  /// **'சுயாதீன மதிப்பீடு'**
  String get gateEvaluation;

  /// No description provided for @gatePassed.
  ///
  /// In ta, this message translates to:
  /// **'முடிந்தது'**
  String get gatePassed;

  /// No description provided for @gateNotPassed.
  ///
  /// In ta, this message translates to:
  /// **'இன்னும் முடியவில்லை'**
  String get gateNotPassed;

  /// No description provided for @assistantUnavailable.
  ///
  /// In ta, this message translates to:
  /// **'உதவியாளர் சேவை தற்போது கிடைக்கவில்லை'**
  String get assistantUnavailable;

  /// No description provided for @assistantError.
  ///
  /// In ta, this message translates to:
  /// **'பதிலைப் பெற முடியவில்லை. மீண்டும் முயற்சிக்கவும்.'**
  String get assistantError;

  /// No description provided for @assistantIntro.
  ///
  /// In ta, this message translates to:
  /// **'பயிர், வானிலை, திட்டங்கள் பற்றி தமிழிலோ ஆங்கிலத்திலோ கேளுங்கள்.'**
  String get assistantIntro;

  /// No description provided for @assistantSuggestions.
  ///
  /// In ta, this message translates to:
  /// **'இவற்றில் ஒன்றைக் கேட்கலாம்:'**
  String get assistantSuggestions;

  /// No description provided for @assistantHint.
  ///
  /// In ta, this message translates to:
  /// **'உங்கள் கேள்வியை எழுதுங்கள்'**
  String get assistantHint;

  /// No description provided for @assistantSend.
  ///
  /// In ta, this message translates to:
  /// **'அனுப்பு'**
  String get assistantSend;

  /// No description provided for @assistantNewChat.
  ///
  /// In ta, this message translates to:
  /// **'புதிய உரையாடல்'**
  String get assistantNewChat;

  /// No description provided for @assistantSources.
  ///
  /// In ta, this message translates to:
  /// **'ஆதாரங்கள்'**
  String get assistantSources;

  /// No description provided for @assistantFallbackNote.
  ///
  /// In ta, this message translates to:
  /// **'இந்தப் பதிலுக்குச் சரிபார்க்கப்பட்ட ஆதாரம் கிடைக்கவில்லை. வேளாண் அலுவலரிடம் உறுதி செய்யவும்.'**
  String get assistantFallbackNote;

  /// No description provided for @suggest1.
  ///
  /// In ta, this message translates to:
  /// **'நெல் நாற்றங்காலை எப்படித் தயாரிப்பது?'**
  String get suggest1;

  /// No description provided for @suggest2.
  ///
  /// In ta, this message translates to:
  /// **'இந்த வாரம் மழை பெய்யுமா?'**
  String get suggest2;

  /// No description provided for @suggest3.
  ///
  /// In ta, this message translates to:
  /// **'எனக்குப் பொருந்தும் அரசு திட்டங்கள் எவை?'**
  String get suggest3;

  /// No description provided for @suggest4.
  ///
  /// In ta, this message translates to:
  /// **'மண் பரிசோதனை ஏன் செய்ய வேண்டும்?'**
  String get suggest4;

  /// No description provided for @stageStarting.
  ///
  /// In ta, this message translates to:
  /// **'தொடங்குகிறது…'**
  String get stageStarting;

  /// No description provided for @stageUnderstanding.
  ///
  /// In ta, this message translates to:
  /// **'கேள்வியைப் புரிந்துகொள்கிறது…'**
  String get stageUnderstanding;

  /// No description provided for @stagePlanning.
  ///
  /// In ta, this message translates to:
  /// **'திட்டமிடுகிறது…'**
  String get stagePlanning;

  /// No description provided for @stageGathering.
  ///
  /// In ta, this message translates to:
  /// **'தகவல் சேகரிக்கிறது…'**
  String get stageGathering;

  /// No description provided for @stageEvidence.
  ///
  /// In ta, this message translates to:
  /// **'ஆதாரங்களைச் சரிபார்க்கிறது…'**
  String get stageEvidence;

  /// No description provided for @stageGrounding.
  ///
  /// In ta, this message translates to:
  /// **'ஆதாரங்களுடன் ஒப்பிடுகிறது…'**
  String get stageGrounding;

  /// No description provided for @stageWriting.
  ///
  /// In ta, this message translates to:
  /// **'பதில் எழுதுகிறது…'**
  String get stageWriting;

  /// No description provided for @voiceStart.
  ///
  /// In ta, this message translates to:
  /// **'குரலில் கேளுங்கள்'**
  String get voiceStart;

  /// No description provided for @voiceStop.
  ///
  /// In ta, this message translates to:
  /// **'நிறுத்து'**
  String get voiceStop;

  /// No description provided for @voiceListening.
  ///
  /// In ta, this message translates to:
  /// **'கேட்கிறது…'**
  String get voiceListening;

  /// No description provided for @voiceThinking.
  ///
  /// In ta, this message translates to:
  /// **'சிந்திக்கிறது…'**
  String get voiceThinking;

  /// No description provided for @voiceSpeaking.
  ///
  /// In ta, this message translates to:
  /// **'பதில் கூறுகிறது…'**
  String get voiceSpeaking;

  /// No description provided for @voiceModeOn.
  ///
  /// In ta, this message translates to:
  /// **'குரல் உரையாடல் முறை ஆன்'**
  String get voiceModeOn;

  /// No description provided for @voiceModeOff.
  ///
  /// In ta, this message translates to:
  /// **'குரல் உரையாடல் முறை ஆஃப்'**
  String get voiceModeOff;

  /// No description provided for @voicePermissionDenied.
  ///
  /// In ta, this message translates to:
  /// **'மைக்ரோஃபோன் அனுமதி இல்லை. அமைப்புகளில் அனுமதி தரவும்.'**
  String get voicePermissionDenied;

  /// No description provided for @voiceNotAvailable.
  ///
  /// In ta, this message translates to:
  /// **'இந்தக் கைபேசியில் குரல் உள்ளீடு கிடைக்கவில்லை'**
  String get voiceNotAvailable;

  /// No description provided for @speakAnswer.
  ///
  /// In ta, this message translates to:
  /// **'பதிலைக் கேளுங்கள்'**
  String get speakAnswer;

  /// No description provided for @ttsNotAvailable.
  ///
  /// In ta, this message translates to:
  /// **'இந்த மொழிக்கு குரல் வாசிப்பு கிடைக்கவில்லை'**
  String get ttsNotAvailable;

  /// No description provided for @scanCrop.
  ///
  /// In ta, this message translates to:
  /// **'பயிர்'**
  String get scanCrop;

  /// No description provided for @scanPaddyExcluded.
  ///
  /// In ta, this message translates to:
  /// **'நெல்லுக்கான ஸ்கேன் தற்போது இல்லை'**
  String get scanPaddyExcluded;

  /// No description provided for @scanCamera.
  ///
  /// In ta, this message translates to:
  /// **'படம் எடு'**
  String get scanCamera;

  /// No description provided for @scanGallery.
  ///
  /// In ta, this message translates to:
  /// **'கேலரியிலிருந்து'**
  String get scanGallery;

  /// No description provided for @scanYourPhoto.
  ///
  /// In ta, this message translates to:
  /// **'நீங்கள் எடுத்த படம்'**
  String get scanYourPhoto;

  /// No description provided for @scanRetake.
  ///
  /// In ta, this message translates to:
  /// **'மீண்டும் எடு'**
  String get scanRetake;

  /// No description provided for @scanRemove.
  ///
  /// In ta, this message translates to:
  /// **'நீக்கு'**
  String get scanRemove;

  /// No description provided for @scanSubmit.
  ///
  /// In ta, this message translates to:
  /// **'பரிசோதனைக்கு அனுப்பு'**
  String get scanSubmit;

  /// No description provided for @scanPickCropFirst.
  ///
  /// In ta, this message translates to:
  /// **'முதலில் பயிரைத் தேர்ந்தெடுக்கவும்'**
  String get scanPickCropFirst;

  /// No description provided for @scanUploading.
  ///
  /// In ta, this message translates to:
  /// **'பதிவேற்றுகிறது…'**
  String get scanUploading;

  /// No description provided for @scanUploadingPct.
  ///
  /// In ta, this message translates to:
  /// **'பதிவேற்றுகிறது… {pct}%'**
  String scanUploadingPct(int pct);

  /// No description provided for @scanModelUnavailable.
  ///
  /// In ta, this message translates to:
  /// **'சரிபார்க்கப்பட்ட நோய் கண்டறியும் மாதிரி இன்னும் கிடைக்கவில்லை. உள்ளூர் வேளாண் அலுவலரை அணுகவும்.'**
  String get scanModelUnavailable;

  /// No description provided for @scanUnsure.
  ///
  /// In ta, this message translates to:
  /// **'உறுதியாகச் சொல்ல முடியவில்லை. வேளாண் அலுவலரை அணுகவும்.'**
  String get scanUnsure;

  /// No description provided for @scanImageTooLarge.
  ///
  /// In ta, this message translates to:
  /// **'படம் மிகப் பெரியது. சிறிய படத்தை முயற்சிக்கவும்.'**
  String get scanImageTooLarge;

  /// No description provided for @scanUnsupportedImage.
  ///
  /// In ta, this message translates to:
  /// **'இந்தப் படத்தைப் பயன்படுத்த முடியாது. JPEG, PNG அல்லது WebP படத்தை முயற்சிக்கவும்.'**
  String get scanUnsupportedImage;

  /// No description provided for @scanPickFailed.
  ///
  /// In ta, this message translates to:
  /// **'படத்தைப் பெற முடியவில்லை'**
  String get scanPickFailed;

  /// No description provided for @cameraPermissionDenied.
  ///
  /// In ta, this message translates to:
  /// **'கேமரா அனுமதி இல்லை. அமைப்புகளில் அனுமதி தரவும்.'**
  String get cameraPermissionDenied;

  /// No description provided for @galleryPermissionDenied.
  ///
  /// In ta, this message translates to:
  /// **'படங்களை அணுக அனுமதி இல்லை'**
  String get galleryPermissionDenied;

  /// No description provided for @scanResultTitle.
  ///
  /// In ta, this message translates to:
  /// **'மாதிரியின் முடிவு'**
  String get scanResultTitle;

  /// No description provided for @scanProbability.
  ///
  /// In ta, this message translates to:
  /// **'நிகழ்தகவு'**
  String get scanProbability;

  /// No description provided for @scanModelVersion.
  ///
  /// In ta, this message translates to:
  /// **'மாதிரிப் பதிப்பு'**
  String get scanModelVersion;

  /// No description provided for @scanInferredAt.
  ///
  /// In ta, this message translates to:
  /// **'கணித்த நேரம்'**
  String get scanInferredAt;

  /// No description provided for @scanGuidance.
  ///
  /// In ta, this message translates to:
  /// **'வழிகாட்டுதல்'**
  String get scanGuidance;

  /// No description provided for @scanConfirmWithOfficer.
  ///
  /// In ta, this message translates to:
  /// **'நடவடிக்கைக்கு முன் வேளாண் அலுவலரிடம் உறுதி செய்யவும்.'**
  String get scanConfirmWithOfficer;

  /// No description provided for @errValueOutOfRange.
  ///
  /// In ta, this message translates to:
  /// **'ஒரு மதிப்பு அனுமதிக்கப்பட்ட வரம்பிற்கு வெளியே உள்ளது. சரிபார்க்கவும்.'**
  String get errValueOutOfRange;

  /// No description provided for @weatherIssuedNotProvided.
  ///
  /// In ta, this message translates to:
  /// **'முன்னறிவிப்பு வெளியான நேரம் வழங்கப்படவில்லை'**
  String get weatherIssuedNotProvided;

  /// No description provided for @weatherIssuedAt.
  ///
  /// In ta, this message translates to:
  /// **'முன்னறிவிப்பு வெளியானது {time}'**
  String weatherIssuedAt(String time);

  /// No description provided for @marketVariety.
  ///
  /// In ta, this message translates to:
  /// **'ரகம்'**
  String get marketVariety;

  /// No description provided for @marketVarietyValue.
  ///
  /// In ta, this message translates to:
  /// **'ரகம்: {variety}'**
  String marketVarietyValue(String variety);

  /// No description provided for @schemeStatus.
  ///
  /// In ta, this message translates to:
  /// **'நிலை (மூலத்தில்)'**
  String get schemeStatus;

  /// No description provided for @schemeActiveOnSource.
  ///
  /// In ta, this message translates to:
  /// **'மூலத்தில் செயலில் உள்ளது'**
  String get schemeActiveOnSource;

  /// No description provided for @schemeStatusNotStated.
  ///
  /// In ta, this message translates to:
  /// **'மூலத்தில் நிலை குறிப்பிடப்படவில்லை'**
  String get schemeStatusNotStated;

  /// No description provided for @schemeComponents.
  ///
  /// In ta, this message translates to:
  /// **'திட்டக் கூறுகள்'**
  String get schemeComponents;

  /// No description provided for @eligibilitySignIn.
  ///
  /// In ta, this message translates to:
  /// **'தகுதியைச் சரிபார்க்க மீண்டும் உள்நுழையவும்'**
  String get eligibilitySignIn;

  /// No description provided for @soilSurvey.
  ///
  /// In ta, this message translates to:
  /// **'ஆய்வு'**
  String get soilSurvey;

  /// No description provided for @soilCycle.
  ///
  /// In ta, this message translates to:
  /// **'சுழற்சி'**
  String get soilCycle;

  /// No description provided for @soilParamSamples.
  ///
  /// In ta, this message translates to:
  /// **'{param} ({samples} மாதிரிகள்)'**
  String soilParamSamples(String param, int samples);

  /// No description provided for @soilLow.
  ///
  /// In ta, this message translates to:
  /// **'குறைவு'**
  String get soilLow;

  /// No description provided for @soilMedium.
  ///
  /// In ta, this message translates to:
  /// **'நடுத்தரம்'**
  String get soilMedium;

  /// No description provided for @soilHigh.
  ///
  /// In ta, this message translates to:
  /// **'அதிகம்'**
  String get soilHigh;

  /// No description provided for @homeGreeting.
  ///
  /// In ta, this message translates to:
  /// **'வணக்கம், {name}'**
  String homeGreeting(String name);

  /// No description provided for @homeGreetingNoName.
  ///
  /// In ta, this message translates to:
  /// **'வணக்கம்'**
  String get homeGreetingNoName;

  /// No description provided for @homeNoFarm.
  ///
  /// In ta, this message translates to:
  /// **'இன்னும் பண்ணை சேர்க்கப்படவில்லை'**
  String get homeNoFarm;

  /// No description provided for @homeSetCrop.
  ///
  /// In ta, this message translates to:
  /// **'சந்தை விலைகளைப் பொருத்த, பண்ணையில் பயிரை அமைக்கவும்'**
  String get homeSetCrop;

  /// No description provided for @homeMarketSnapshot.
  ///
  /// In ta, this message translates to:
  /// **'சந்தை விலைகள் (சமீபத்திய பதிவு)'**
  String get homeMarketSnapshot;

  /// No description provided for @homeMarketNeedsFarm.
  ///
  /// In ta, this message translates to:
  /// **'சந்தை விலைகளைக் காண பண்ணை அல்லது மாவட்டத்தை அமைக்கவும்'**
  String get homeMarketNeedsFarm;

  /// No description provided for @homeRecentActivity.
  ///
  /// In ta, this message translates to:
  /// **'சமீபத்திய செயல்பாடு'**
  String get homeRecentActivity;

  /// No description provided for @homeShortcuts.
  ///
  /// In ta, this message translates to:
  /// **'விரைவு அணுகல்'**
  String get homeShortcuts;

  /// No description provided for @homeSeeAll.
  ///
  /// In ta, this message translates to:
  /// **'அனைத்தும்'**
  String get homeSeeAll;

  /// No description provided for @soilSamplesCount.
  ///
  /// In ta, this message translates to:
  /// **'{count} மாதிரிகள்'**
  String soilSamplesCount(int count);

  /// No description provided for @homeNoMarketForCrop.
  ///
  /// In ta, this message translates to:
  /// **'இந்தப் பயிருக்குச் சந்தை விலைத் தரவு இல்லை'**
  String get homeNoMarketForCrop;

  /// No description provided for @voiceOfflineUnavailable.
  ///
  /// In ta, this message translates to:
  /// **'இந்தக் கைபேசியில் ஆஃப்லைன் குரல் அறிதல் இல்லை. எனவே எதுவும் பதிவு செய்யப்படவில்லை, பதிவேற்றப்படவில்லை. கேள்வியை தட்டச்சு செய்யவும்.'**
  String get voiceOfflineUnavailable;

  /// No description provided for @voiceOfflineLanguageMissing.
  ///
  /// In ta, this message translates to:
  /// **'இந்த மொழிக்கான ஆஃப்லைன் பேச்சுத் தொகுப்பு நிறுவப்படவில்லை. கைபேசியின் பேச்சு அமைப்புகளில் நிறுவவும் (எ.கா. Google ஆப் > Settings > Voice > Offline speech recognition). அதுவரை கேள்வியை தட்டச்சு செய்யலாம்.'**
  String get voiceOfflineLanguageMissing;

  /// No description provided for @voiceTtsMissingTamil.
  ///
  /// In ta, this message translates to:
  /// **'ஆஃப்லைன் தமிழ் குரல் நிறுவப்படவில்லை, அதனால் பதிலை வாசிக்க முடியவில்லை. நிறுவ: Settings > General management > Text-to-speech output > engine settings > Install voice data > Tamil.'**
  String get voiceTtsMissingTamil;

  /// No description provided for @voiceTtsMissingEnglish.
  ///
  /// In ta, this message translates to:
  /// **'ஆஃப்லைன் ஆங்கிலக் குரல் நிறுவப்படவில்லை, அதனால் பதிலை வாசிக்க முடியவில்லை. நிறுவ: Settings > General management > Text-to-speech output > engine settings > Install voice data.'**
  String get voiceTtsMissingEnglish;

  /// No description provided for @voiceTtsFailed.
  ///
  /// In ta, this message translates to:
  /// **'பதிலை வாசிக்க முடியவில்லை. ஒலிபெருக்கி படத்தைத் தட்டி மீண்டும் முயற்சிக்கவும்.'**
  String get voiceTtsFailed;

  /// No description provided for @voiceSttError.
  ///
  /// In ta, this message translates to:
  /// **'குரல் உள்ளீடு எதிர்பாராமல் நின்றது. மீண்டும் முயற்சிக்கவும் அல்லது தட்டச்சு செய்யவும்.'**
  String get voiceSttError;

  /// No description provided for @voiceDismiss.
  ///
  /// In ta, this message translates to:
  /// **'மூடு'**
  String get voiceDismiss;

  /// No description provided for @brandTagline.
  ///
  /// In ta, this message translates to:
  /// **'தமிழ்நாட்டு விவசாயிகளுக்கான வழிகாட்டுதல், தமிழிலும் ஆங்கிலத்திலும்'**
  String get brandTagline;

  /// No description provided for @loginPhoneHelp.
  ///
  /// In ta, this message translates to:
  /// **'இந்த எண்ணுக்கு ஒருமுறை குறியீடு அனுப்பப்படும். கடவுச்சொல் தேவையில்லை.'**
  String get loginPhoneHelp;

  /// No description provided for @homeFarmLabel.
  ///
  /// In ta, this message translates to:
  /// **'உங்கள் நிலம்'**
  String get homeFarmLabel;

  /// No description provided for @homeAskTitle.
  ///
  /// In ta, this message translates to:
  /// **'வேளாண் உதவியாளரிடம் கேளுங்கள்'**
  String get homeAskTitle;

  /// No description provided for @homeAskSubtitle.
  ///
  /// In ta, this message translates to:
  /// **'பயிர், மண், வானிலை, திட்டங்கள். ஆதாரங்கள் கிடைத்தால் காட்டப்படும்.'**
  String get homeAskSubtitle;

  /// No description provided for @homeAskAction.
  ///
  /// In ta, this message translates to:
  /// **'கேள்வி கேளுங்கள்'**
  String get homeAskAction;

  /// No description provided for @homeServices.
  ///
  /// In ta, this message translates to:
  /// **'சேவைகள்'**
  String get homeServices;

  /// No description provided for @moreInfoSection.
  ///
  /// In ta, this message translates to:
  /// **'விவசாயத் தகவல்'**
  String get moreInfoSection;

  /// No description provided for @moreRecordsSection.
  ///
  /// In ta, this message translates to:
  /// **'உங்கள் பதிவுகள்'**
  String get moreRecordsSection;

  /// No description provided for @moreAccountSection.
  ///
  /// In ta, this message translates to:
  /// **'கணக்கு'**
  String get moreAccountSection;

  /// No description provided for @moreWeatherSub.
  ///
  /// In ta, this message translates to:
  /// **'தற்போதைய நிலை மற்றும் 7 நாள் முன்னறிவிப்பு'**
  String get moreWeatherSub;

  /// No description provided for @moreMarketSub.
  ///
  /// In ta, this message translates to:
  /// **'பதிவான விலைகள்; நேரடி விலை அல்ல'**
  String get moreMarketSub;

  /// No description provided for @moreSchemesSub.
  ///
  /// In ta, this message translates to:
  /// **'மத்திய, மாநில திட்டங்கள்'**
  String get moreSchemesSub;

  /// No description provided for @moreSoilSub.
  ///
  /// In ta, this message translates to:
  /// **'பகுதி மண் தகவல் மற்றும் உங்கள் மண் பரிசோதனைகள்'**
  String get moreSoilSub;

  /// No description provided for @moreScanSub.
  ///
  /// In ta, this message translates to:
  /// **'சரிபார்ப்பில் உள்ளது; நோய் கண்டறிதல் இன்னும் இல்லை'**
  String get moreScanSub;

  /// No description provided for @moreFarmsSub.
  ///
  /// In ta, this message translates to:
  /// **'நிலங்களைச் சேர்க்க அல்லது திருத்த'**
  String get moreFarmsSub;

  /// No description provided for @moreDiarySub.
  ///
  /// In ta, this message translates to:
  /// **'குறிப்புகள் மற்றும் பண்ணை நடவடிக்கைகள்'**
  String get moreDiarySub;

  /// No description provided for @moreSatelliteSub.
  ///
  /// In ta, this message translates to:
  /// **'செயற்கைக்கோள் வசதிகளின் நிலை'**
  String get moreSatelliteSub;

  /// No description provided for @moreProfileSub.
  ///
  /// In ta, this message translates to:
  /// **'பெயர், மாவட்டம், மொழி'**
  String get moreProfileSub;

  /// No description provided for @moreSettingsSub.
  ///
  /// In ta, this message translates to:
  /// **'மொழி, தோற்றம், பற்றி'**
  String get moreSettingsSub;

  /// No description provided for @assistantEmptyTitle.
  ///
  /// In ta, this message translates to:
  /// **'உங்கள் விவசாயத்திற்கு எப்படி உதவலாம்?'**
  String get assistantEmptyTitle;

  /// No description provided for @assistantCopy.
  ///
  /// In ta, this message translates to:
  /// **'பதிலை நகலெடு'**
  String get assistantCopy;

  /// No description provided for @assistantCopied.
  ///
  /// In ta, this message translates to:
  /// **'பதில் நகலெடுக்கப்பட்டது'**
  String get assistantCopied;

  /// No description provided for @assistantGeneralGuidance.
  ///
  /// In ta, this message translates to:
  /// **'பொது வழிகாட்டுதல்'**
  String get assistantGeneralGuidance;

  /// No description provided for @assistantGeneralGuidanceNote.
  ///
  /// In ta, this message translates to:
  /// **'TNAU ஆதாரம் இல்லாமல்'**
  String get assistantGeneralGuidanceNote;

  /// No description provided for @assistantSourcesNote.
  ///
  /// In ta, this message translates to:
  /// **'இந்தப் பதிலுக்காகப் பெறப்பட்ட ஆவணங்கள். ஒவ்வொரு வாக்கியத்தையும் இவை உறுதிப்படுத்தாமல் இருக்கலாம்.'**
  String get assistantSourcesNote;

  /// No description provided for @assistantNoAnswerTitle.
  ///
  /// In ta, this message translates to:
  /// **'சரிபார்க்கப்பட்ட பதில் இல்லை'**
  String get assistantNoAnswerTitle;

  /// No description provided for @voiceTapToStop.
  ///
  /// In ta, this message translates to:
  /// **'நிறுத்த தட்டவும்'**
  String get voiceTapToStop;

  /// No description provided for @voiceSpeakAnswer.
  ///
  /// In ta, this message translates to:
  /// **'கேளுங்கள்'**
  String get voiceSpeakAnswer;

  /// No description provided for @scanValidationBadge.
  ///
  /// In ta, this message translates to:
  /// **'சரிபார்ப்பில் உள்ளது'**
  String get scanValidationBadge;

  /// No description provided for @scanValidationTitle.
  ///
  /// In ta, this message translates to:
  /// **'நோய் கண்டறிதல் இன்னும் கிடைக்கவில்லை'**
  String get scanValidationTitle;

  /// No description provided for @scanValidationBody.
  ///
  /// In ta, this message translates to:
  /// **'நோய் மாதிரி விவசாயிகள் பயன்பாட்டிற்கு இன்னும் அங்கீகரிக்கப்படவில்லை. நீங்கள் அனுப்பும் புகைப்படத்திற்கு நோய் கண்டறிதல் வழங்கப்படாது. பயிர் பிரச்சனைக்கு உங்கள் பகுதி வேளாண் அலுவலரை அணுகவும்.'**
  String get scanValidationBody;

  /// No description provided for @scanHowTitle.
  ///
  /// In ta, this message translates to:
  /// **'இங்கே என்ன செய்யலாம்'**
  String get scanHowTitle;

  /// No description provided for @scanHowBody.
  ///
  /// In ta, this message translates to:
  /// **'பயிரையும் பாதிக்கப்பட்ட இலையின் தெளிவான புகைப்படத்தையும் தேர்ந்தெடுக்கவும். சரிபார்க்கப்பட்ட முடிவு கிடைக்குமா என்பதை ஆப் நேர்மையாகத் தெரிவிக்கும்.'**
  String get scanHowBody;

  /// No description provided for @marketSnapshotBadge.
  ///
  /// In ta, this message translates to:
  /// **'பதிவான விலை; நேரடி அல்ல'**
  String get marketSnapshotBadge;

  /// No description provided for @settingsAppearance.
  ///
  /// In ta, this message translates to:
  /// **'தோற்றம்'**
  String get settingsAppearance;

  /// No description provided for @settingsPrivacy.
  ///
  /// In ta, this message translates to:
  /// **'தனியுரிமை'**
  String get settingsPrivacy;

  /// No description provided for @settingsPrivacyBody.
  ///
  /// In ta, this message translates to:
  /// **'உங்கள் கேள்விகளுக்கு UZHAVAN சேவையகத்தில் இயங்கும் மாதிரி பதிலளிக்கிறது; கட்டண மேகக்கணி AI சேவை பயன்படுத்தப்படவில்லை. பேச்சு இந்தக் கைபேசியின் சொந்தக் குரலில் உருவாகிறது. வானிலை Open-Meteo-விலிருந்து, உங்கள் மாவட்ட இருப்பிடத்தை மட்டும் பயன்படுத்திப் பெறப்படுகிறது.'**
  String get settingsPrivacyBody;

  /// No description provided for @settingsVoice.
  ///
  /// In ta, this message translates to:
  /// **'குரல்'**
  String get settingsVoice;

  /// No description provided for @settingsVoiceBody.
  ///
  /// In ta, this message translates to:
  /// **'பதில்கள் இந்தக் கைபேசியின் குரலில் வாசிக்கப்படும். குரல் உள்ளீட்டிற்கு Android 12 அல்லது புதியதும் ஆஃப்லைன் மொழித் தொகுப்பும் தேவை; இல்லையெனில் கேள்வியைத் தட்டச்சு செய்யவும்.'**
  String get settingsVoiceBody;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'ta'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'ta':
      return AppLocalizationsTa();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
