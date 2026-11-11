// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Tamil (`ta`).
class AppLocalizationsTa extends AppLocalizations {
  AppLocalizationsTa([String locale = 'ta']) : super(locale);

  @override
  String get appTitle => 'UZHAVAN AI';

  @override
  String get languageSwitchLabel => 'தமிழ் → English';

  @override
  String get languageSwitchTooltip => 'மொழியை மாற்று';

  @override
  String get languageTamil => 'தமிழ்';

  @override
  String get languageEnglish => 'English';

  @override
  String get notSet => 'அமைக்கப்படவில்லை';

  @override
  String get optionalSuffix => '(விருப்பம்)';

  @override
  String get retry => 'மீண்டும் முயற்சி';

  @override
  String get loading => 'ஏற்றுகிறது…';

  @override
  String get stateError => 'ஏதோ தவறு நடந்தது';

  @override
  String get stateUnsure =>
      'உறுதியாகச் சொல்ல முடியவில்லை: வேளாண் அலுவலரை அணுகவும்';

  @override
  String get stateUnavailable => 'இந்தச் சேவை தற்போது கிடைக்கவில்லை';

  @override
  String get stateEmpty => 'காட்ட எதுவும் இல்லை';

  @override
  String get comingSoon => 'இந்த வசதி அடுத்த புதுப்பிப்பில் வரும்';

  @override
  String get navHome => 'முகப்பு';

  @override
  String get navAssistant => 'உதவி';

  @override
  String get navScan => 'ஸ்கேன்';

  @override
  String get navMarket => 'சந்தை';

  @override
  String get navMore => 'மேலும்';

  @override
  String get featureHome => 'முகப்பு';

  @override
  String get featureAssistant => 'வேளாண் உதவியாளர்';

  @override
  String get featureScan => 'பயிர் நோய் ஸ்கேன்';

  @override
  String get featureMarket => 'சந்தை விலைகள்';

  @override
  String get featureWeather => 'வானிலை';

  @override
  String get featureSchemes => 'அரசு திட்டங்கள்';

  @override
  String get featureSoil => 'மண்';

  @override
  String get featureFarms => 'என் பண்ணைகள்';

  @override
  String get featureDiary => 'பண்ணை நாட்குறிப்பு';

  @override
  String get featureSatellite => 'செயற்கைக்கோள்';

  @override
  String get featureProfile => 'சுயவிவரம்';

  @override
  String get featureSettings => 'அமைப்புகள்';

  @override
  String get back => 'பின்செல்';

  @override
  String get loginTitle => 'உள்நுழைக';

  @override
  String get loginSubtitle => 'உங்கள் தொலைபேசி எண்ணை உள்ளிடுங்கள்';

  @override
  String get phoneLabel => 'தொலைபேசி எண்';

  @override
  String get phonePrefix => '+91';

  @override
  String get phoneHint => '10 இலக்க எண்';

  @override
  String get phoneInvalid =>
      '6, 7, 8 அல்லது 9 இல் தொடங்கும் 10 இலக்க எண்ணை உள்ளிடுங்கள்';

  @override
  String get sendOtp => 'OTP அனுப்பு';

  @override
  String get otpTitle => 'தொலைபேசி சரிபார்ப்பு';

  @override
  String otpSentTo(String phone) {
    return '+91 $phone க்கு OTP அனுப்பப்பட்டது';
  }

  @override
  String get otpLabel => '6 இலக்க OTP';

  @override
  String get otpInvalid => '6 இலக்கக் குறியீட்டை உள்ளிடுங்கள்';

  @override
  String get verify => 'சரிபார்';

  @override
  String get resendOtp => 'குறியீட்டை மீண்டும் அனுப்பு';

  @override
  String resendIn(int seconds) {
    return '$seconds வினாடிகளில் மீண்டும் அனுப்பலாம்';
  }

  @override
  String get changeNumber => 'எண்ணை மாற்று';

  @override
  String get otpResent => 'புதிய குறியீடு அனுப்பப்பட்டது';

  @override
  String get errOtpIncorrect => 'தவறான குறியீடு. மீண்டும் முயற்சிக்கவும்.';

  @override
  String get errOtpExpired =>
      'குறியீடு காலாவதியானது. புதிய குறியீட்டைக் கோருங்கள்.';

  @override
  String get errOtpAttemptsExceeded =>
      'பல தவறான முயற்சிகள். புதிய குறியீட்டைக் கோருங்கள்.';

  @override
  String get errOtpNotFound =>
      'செயலில் உள்ள குறியீடு இல்லை. புதிய குறியீட்டைக் கோருங்கள்.';

  @override
  String get errRateLimited =>
      'பல கோரிக்கைகள். சிறிது நேரம் கழித்து முயற்சிக்கவும்.';

  @override
  String errRateLimitedSeconds(int seconds) {
    return 'பல கோரிக்கைகள். $seconds வினாடிகளில் மீண்டும் முயற்சிக்கவும்.';
  }

  @override
  String errRateLimitedMinutes(int minutes) {
    return 'பல கோரிக்கைகள். $minutes நிமிடங்களில் மீண்டும் முயற்சிக்கவும்.';
  }

  @override
  String get errOtpDeliveryNotConfigured =>
      'SMS சேவை தற்போது கிடைக்கவில்லை. பின்னர் முயற்சிக்கவும்.';

  @override
  String get errServerUnreachable => 'UZHAVAN சேவையகத்தை அணுக முடியவில்லை';

  @override
  String get errSessionExpired =>
      'உங்கள் அமர்வு முடிந்தது. மீண்டும் உள்நுழையவும்.';

  @override
  String get errValidation => 'உள்ளிட்ட விவரங்களைச் சரிபார்க்கவும்';

  @override
  String get errNotFound => 'கோரிய தகவல் கிடைக்கவில்லை';

  @override
  String get profileName => 'பெயர்';

  @override
  String get profileDistrict => 'மாவட்டம்';

  @override
  String get profileVillage => 'கிராமம்';

  @override
  String get profilePhone => 'தொலைபேசி';

  @override
  String get profileLanguage => 'விருப்ப மொழி';

  @override
  String get profileEdit => 'சுயவிவரத்தைத் திருத்து';

  @override
  String get profileUnavailable => 'சுயவிவரத் தரவு கிடைக்கவில்லை';

  @override
  String get profileStillIncomplete =>
      'சுயவிவரம் இன்னும் முழுமையடையவில்லை. தேவையான விவரங்களை நிரப்பவும்.';

  @override
  String get onboardingTitle => 'உங்கள் விவரங்கள்';

  @override
  String get onboardingSubtitle => 'சிறந்த ஆலோசனைக்கு உதவும்';

  @override
  String get onboardingContinue => 'தொடரவும்';

  @override
  String get nameInvalid => 'பெயர் 2 முதல் 100 எழுத்துகள் இருக்க வேண்டும்';

  @override
  String get districtRequired => 'மாவட்டத்தைத் தேர்ந்தெடுக்கவும்';

  @override
  String get districtPickerTitle => 'மாவட்டத்தைத் தேர்ந்தெடுக்கவும்';

  @override
  String get searchHint => 'தேடு';

  @override
  String get districtsUnavailable => 'மாவட்டப் பட்டியல் கிடைக்கவில்லை';

  @override
  String get optionsUnavailable => 'தேர்வுப் பட்டியல் கிடைக்கவில்லை';

  @override
  String get noMatches => 'பொருத்தம் எதுவும் இல்லை';

  @override
  String get pickerNone => 'தேர்வு செய்யவில்லை';

  @override
  String get save => 'சேமி';

  @override
  String get cancel => 'ரத்து செய்';

  @override
  String get saved => 'சேமிக்கப்பட்டது';

  @override
  String get delete => 'நீக்கு';

  @override
  String get edit => 'திருத்து';

  @override
  String get logout => 'வெளியேறு';

  @override
  String get logoutConfirm => 'UZHAVAN AI இலிருந்து வெளியேற வேண்டுமா?';

  @override
  String get farmAdd => 'பண்ணையைச் சேர்';

  @override
  String get farmEdit => 'பண்ணையைத் திருத்து';

  @override
  String farmDeleteConfirm(String name) {
    return '\"$name\" பண்ணையை நீக்க வேண்டுமா?';
  }

  @override
  String get farmDeleted => 'பண்ணை நீக்கப்பட்டது';

  @override
  String get farmsEmpty => 'இன்னும் பண்ணைகள் சேர்க்கப்படவில்லை';

  @override
  String get farmsUnavailable => 'பண்ணை தரவு கிடைக்கவில்லை';

  @override
  String get farmName => 'பண்ணையின் பெயர்';

  @override
  String get farmNameRequired => 'பண்ணையின் பெயரை உள்ளிடுங்கள்';

  @override
  String get farmLocation => 'இருப்பிடம்';

  @override
  String get farmLocationHelp =>
      'அட்சரேகை, தீர்க்கரேகை இரண்டையும் உள்ளிடுங்கள் அல்லது இரண்டையும் காலியாக விடுங்கள்';

  @override
  String get farmLatitude => 'அட்சரேகை';

  @override
  String get farmLongitude => 'தீர்க்கரேகை';

  @override
  String get farmLatInvalid =>
      'அட்சரேகை 8.0 முதல் 13.6 வரை இருக்க வேண்டும் (தமிழ்நாடு)';

  @override
  String get farmLonInvalid =>
      'தீர்க்கரேகை 76.2 முதல் 80.4 வரை இருக்க வேண்டும் (தமிழ்நாடு)';

  @override
  String get farmLatLonPair => 'அட்சரேகை, தீர்க்கரேகை இரண்டும் தேவை';

  @override
  String farmCoordinatesValue(String lat, String lon) {
    return '$lat, $lon';
  }

  @override
  String get farmArea => 'நில அளவு (ஏக்கர்)';

  @override
  String get farmAreaInvalid => 'சரியான ஏக்கர் அளவை உள்ளிடுங்கள்';

  @override
  String farmAreaValue(String acres) {
    return '$acres ஏக்கர்';
  }

  @override
  String get farmCrop => 'பயிர்';

  @override
  String get farmStage => 'பயிர் நிலை';

  @override
  String get farmSeason => 'பருவம்';

  @override
  String get farmIrrigation => 'பாசன வகை';

  @override
  String get settingsLanguage => 'மொழி';

  @override
  String get settingsTheme => 'தீம்';

  @override
  String get themeLight => 'வெளிச்சம்';

  @override
  String get themeDark => 'இருள்';

  @override
  String get themeSystem => 'சாதன அமைப்பு';

  @override
  String get settingsAbout => 'பயன்பாட்டைப் பற்றி';

  @override
  String get aboutDescription => 'தமிழ்நாடு விவசாயிகளுக்கான வேளாண் உதவியாளர்';

  @override
  String appVersion(String version) {
    return 'பதிப்பு $version';
  }

  @override
  String apiBaseUrlDebug(String url) {
    return 'API முகவரி (டீபக்): $url';
  }

  @override
  String get configErrorTitle => 'அமைப்புப் பிழை';

  @override
  String get configErrorInsecure =>
      'இந்த வெளியீட்டுப் பதிப்புக்கு பாதுகாப்பான (https) API முகவரி தேவை.';

  @override
  String get configErrorInvalid => 'API முகவரி தவறானது.';

  @override
  String configErrorDetail(String url) {
    return 'API_BASE_URL: $url';
  }

  @override
  String get farmLimitReached => 'அதிகபட்சம் 5 பண்ணைகள் மட்டுமே சேர்க்கலாம்';

  @override
  String get errInvalidDistrict => 'தேர்ந்தெடுத்த மாவட்டம் சரியானதல்ல';

  @override
  String get errInvalidLanguage => 'தேர்ந்தெடுத்த மொழி சரியானதல்ல';

  @override
  String get errInvalidVillage => 'கிராமத்தின் பெயரைச் சரிபார்க்கவும்';

  @override
  String get errInvalidLocation => 'இருப்பிட மதிப்புகள் சரியானவை அல்ல';

  @override
  String get errLocationOutsideTn =>
      'இருப்பிடம் தமிழ்நாட்டுக்குள் இருக்க வேண்டும்';

  @override
  String get errInvalidBoundary => 'பண்ணை எல்லை சரியானதல்ல';

  @override
  String get errInvalidCrop => 'தேர்ந்தெடுத்த பயிர் சரியானதல்ல';

  @override
  String get errInvalidCropStage => 'தேர்ந்தெடுத்த பயிர் நிலை சரியானதல்ல';

  @override
  String get errInvalidSeason => 'தேர்ந்தெடுத்த பருவம் சரியானதல்ல';

  @override
  String get errInvalidIrrigationType => 'தேர்ந்தெடுத்த பாசன வகை சரியானதல்ல';

  @override
  String get notAvailable => 'கிடைக்கவில்லை';

  @override
  String sourceLabel(String source) {
    return 'ஆதாரம்: $source';
  }

  @override
  String updatedAt(String time) {
    return 'புதுப்பித்தது $time';
  }

  @override
  String observedOn(String date) {
    return 'பதிவான நாள் $date';
  }

  @override
  String get oldData => 'பழைய தரவு';

  @override
  String get kindCurrent => 'தற்போது';

  @override
  String get kindForecast => 'முன்னறிவிப்பு';

  @override
  String get kindHistorical => 'கடந்த கால தரவு';

  @override
  String get kindLatestObserved => 'சமீபத்திய பதிவு';

  @override
  String get kindEstimated => 'மாதிரி மதிப்பீடு';

  @override
  String get kindMeasured => 'அளவிடப்பட்டது';

  @override
  String get kindReference => 'குறிப்புத் தகவல்';

  @override
  String get linkOpenFailed => 'இணைப்பைத் திறக்க முடியவில்லை';

  @override
  String get farmPickerLabel => 'பண்ணை';

  @override
  String get locationMissing =>
      'பண்ணையைச் சேர்க்கவும் அல்லது சுயவிவரத்தில் மாவட்டத்தை அமைக்கவும்';

  @override
  String get close => 'மூடு';

  @override
  String get weatherUnavailable => 'வானிலை தரவு தற்போது கிடைக்கவில்லை';

  @override
  String get weatherNow => 'தற்போதைய வானிலை';

  @override
  String weatherLocation(String name) {
    return 'இடம்: $name';
  }

  @override
  String get weatherFeelsLike => 'உணரும் வெப்பம்';

  @override
  String get weatherHumidity => 'ஈரப்பதம்';

  @override
  String get weatherRain => 'மழை';

  @override
  String get weatherWind => 'காற்று';

  @override
  String get weatherModelTime => 'மாதிரி நேரம்';

  @override
  String get weatherForecast7 => '7 நாள் முன்னறிவிப்பு';

  @override
  String get weatherToday => 'இன்றைய முன்னறிவிப்பு';

  @override
  String get weatherForecastEmpty => 'முன்னறிவிப்பு தரவு இல்லை';

  @override
  String weatherMaxMin(String max, String min) {
    return 'அதிகம் $max · குறைவு $min';
  }

  @override
  String weatherRainLine(String mm, String pct) {
    return 'மழை $mm · வாய்ப்பு $pct';
  }

  @override
  String get weatherAdvisories => 'வானிலை அறிவுரைகள்';

  @override
  String get weatherNoAdvisories => 'தற்போது எந்த விதியும் பொருந்தவில்லை';

  @override
  String get severityCaution => 'எச்சரிக்கை';

  @override
  String get severityInfo => 'தகவல்';

  @override
  String ruleSource(String source) {
    return 'விதியின் ஆதாரம்: $source';
  }

  @override
  String get marketUnavailable => 'சந்தை தரவு தற்போது கிடைக்கவில்லை';

  @override
  String get marketEmpty => 'இந்தத் தேர்வுக்கு விலைப் பதிவுகள் இல்லை';

  @override
  String get marketDistrictFilter => 'மாவட்டம்';

  @override
  String get allCommodities => 'அனைத்தும்';

  @override
  String get marketLatestTitle => 'சமீபத்திய விலைப் பதிவுகள்';

  @override
  String get marketTapForTrend =>
      'கடந்த கால விலைப் போக்கைப் பார்க்க ஒரு பதிவைத் தொடவும்';

  @override
  String marketMinMax(String min, String max) {
    return 'குறைந்தது ₹ $min – அதிகம் ₹ $max';
  }

  @override
  String get unitRsPerQuintal => 'ரூ/குவிண்டால்';

  @override
  String unitNoteLabel(String note) {
    return 'அலகுக் குறிப்பு: $note';
  }

  @override
  String get marketTrend => 'விலைப் போக்கு (கடந்த காலம்)';

  @override
  String marketTrendTitle(String name) {
    return '$name: கடந்த கால விலைப் போக்கு';
  }

  @override
  String marketTrendCaption(String market, int days) {
    return '$market · கடந்த $days நாட்கள் · பொதுவான (modal) விலை';
  }

  @override
  String get marketTrendEmpty => 'இந்தச் சந்தைக்குக் கடந்த கால விலைகள் இல்லை';

  @override
  String get schemesUnavailable => 'திட்டத் தரவு தற்போது கிடைக்கவில்லை';

  @override
  String get schemesEmpty => 'இந்தத் தேடலுக்குத் திட்டங்கள் இல்லை';

  @override
  String get schemeSearchHint => 'திட்டங்களைத் தேடுங்கள்';

  @override
  String get levelAll => 'அனைத்தும்';

  @override
  String get levelCentral => 'மத்திய அரசு';

  @override
  String get levelState => 'மாநில அரசு';

  @override
  String get schemeCropFilter => 'பயிர்';

  @override
  String schemesCount(int count) {
    return '$count திட்டங்கள்';
  }

  @override
  String get schemeInactive => 'மூலத்தில் செயலில் இல்லை';

  @override
  String get schemeLevel => 'நிலை';

  @override
  String get schemeAuthority => 'பொறுப்பு அமைப்பு';

  @override
  String get schemeDateChecked => 'சரிபார்த்த நாள்';

  @override
  String get schemeLastUpdatedOnSource => 'மூலத்தில் புதுப்பித்த நாள்';

  @override
  String get schemeOfficialLink => 'அதிகாரப்பூர்வ இணையப் பக்கம்';

  @override
  String get schemeDescription => 'விளக்கம்';

  @override
  String get schemeEligibilityText => 'தகுதி விவரம் (அதிகாரப்பூர்வ உரை)';

  @override
  String get schemeBenefits => 'பயன்கள்';

  @override
  String get schemeHowToApply => 'விண்ணப்பிக்கும் முறை';

  @override
  String get schemeDocuments => 'தேவையான ஆவணங்கள்';

  @override
  String get schemeSourceDocuments => 'மூல ஆவணங்கள்';

  @override
  String get eligibilityTitle => 'உங்கள் தகுதி சரிபார்ப்பு';

  @override
  String get eligibilityUnavailable =>
      'தகுதி சரிபார்ப்பு தற்போது கிடைக்கவில்லை';

  @override
  String get eligMeetsKnown =>
      'அறியப்பட்ட நிபந்தனைகளைப் பூர்த்தி செய்கிறீர்கள்';

  @override
  String get eligFailsKnown => 'அறியப்பட்ட நிபந்தனைகளைப் பூர்த்தி செய்யவில்லை';

  @override
  String get eligMoreInfo => 'மேலும் தகவல் தேவை';

  @override
  String get eligCannotDetermine => 'தீர்மானிக்க முடியவில்லை';

  @override
  String get eligibilityNoResult => 'தகுதி முடிவு கிடைக்கவில்லை';

  @override
  String get eligibilityReasons => 'காரணங்கள்';

  @override
  String get eligibilityMissing => 'தேவைப்படும் விவரங்கள்';

  @override
  String get eligibilityCriteriaSource => 'நிபந்தனைகளின் ஆதாரம்';

  @override
  String get eligibilityDisclaimer =>
      'இது அறியப்பட்ட நிபந்தனைகளை மட்டுமே சரிபார்க்கிறது; இறுதி முடிவு அரசு அலுவலகத்தினுடையது.';

  @override
  String get soilUnavailable => 'மண் தரவு தற்போது கிடைக்கவில்லை';

  @override
  String get soilRegionalTitle => 'பிராந்தியத் தகவல்';

  @override
  String get soilTypes => 'இப்பகுதியின் மண் வகைகள்';

  @override
  String get soilNutrientStatus => 'மாவட்ட ஊட்டச்சத்து நிலை';

  @override
  String get soilNutrientStatusCaption =>
      'ஒவ்வொரு வகையிலும் உள்ள மாதிரிகளின் சதவீதம்';

  @override
  String get soilEstimatedTitle => 'மதிப்பிடப்பட்ட (மாதிரி) மதிப்புகள்';

  @override
  String get soilEstimatedWarning =>
      'இவை கணினி மாதிரி (model) மதிப்பீடுகள், உங்கள் நிலத்தின் அளவீடுகள் அல்ல';

  @override
  String get soilDepth => 'ஆழம்';

  @override
  String get soilMeasuredTitle => 'உங்கள் மண் பரிசோதனைகள் (அளவிடப்பட்டவை)';

  @override
  String get soilNoTests => 'இன்னும் மண் பரிசோதனை முடிவுகள் சேர்க்கப்படவில்லை';

  @override
  String get soilAddTest => 'மண் பரிசோதனை சேர்';

  @override
  String get soilAddTestNeedsFarm =>
      'மண் பரிசோதனை சேர்க்க முதலில் ஒரு பண்ணையைச் சேர்க்கவும்';

  @override
  String soilSampleOn(String date) {
    return 'மாதிரி எடுத்த நாள்: $date';
  }

  @override
  String soilLab(String lab) {
    return 'ஆய்வகம்: $lab';
  }

  @override
  String get soilFarmerEntered => 'நீங்கள் உள்ளிட்டது';

  @override
  String get soilSampleDate => 'மாதிரி எடுத்த நாள்';

  @override
  String get soilPickDate => 'நாளைத் தேர்ந்தெடுக்கவும்';

  @override
  String get soilLabName => 'ஆய்வகத்தின் பெயர்';

  @override
  String get soilValuesHint =>
      'உங்கள் மண் பரிசோதனை அட்டையில் உள்ள மதிப்புகளை மட்டும் உள்ளிடவும்; மற்றவற்றைக் காலியாக விடவும்.';

  @override
  String get soilValueInvalid => 'சரியான எண்ணை உள்ளிடவும்';

  @override
  String soilValueRange(String min, String max) {
    return 'அனுமதி: $min – $max';
  }

  @override
  String get soilFarmRequired => 'பண்ணையைத் தேர்ந்தெடுக்கவும்';

  @override
  String get soilDateRequired => 'மாதிரி எடுத்த நாளைத் தேர்ந்தெடுக்கவும்';

  @override
  String get soilAtLeastOne => 'குறைந்தது ஒரு மதிப்பையாவது உள்ளிடவும்';

  @override
  String get soilPh => 'pH';

  @override
  String get soilSoc => 'மண் கரிமக் கார்பன்';

  @override
  String get soilClay => 'களிமண்';

  @override
  String get soilSand => 'மணல்';

  @override
  String get soilSilt => 'வண்டல்';

  @override
  String get soilCec => 'நேர்மின் அயனி பரிமாற்றத் திறன் (CEC)';

  @override
  String get soilBdod => 'மண் அடர்த்தி';

  @override
  String get soilNitrogenEst => 'மொத்த நைட்ரஜன்';

  @override
  String get soilEc => 'மின் கடத்துத்திறன் (EC)';

  @override
  String get soilOc => 'கரிமக் கார்பன் (OC)';

  @override
  String get soilN => 'தழைச்சத்து (N)';

  @override
  String get soilP => 'மணிச்சத்து (P)';

  @override
  String get soilK => 'சாம்பல்சத்து (K)';

  @override
  String get soilS => 'கந்தகம் (S)';

  @override
  String get soilZn => 'துத்தநாகம் (Zn)';

  @override
  String get soilFe => 'இரும்பு (Fe)';

  @override
  String get soilCu => 'தாமிரம் (Cu)';

  @override
  String get soilMn => 'மாங்கனீசு (Mn)';

  @override
  String get soilB => 'போரான் (B)';

  @override
  String get diaryUnavailable => 'நாட்குறிப்பு தற்போது கிடைக்கவில்லை';

  @override
  String get diaryEmpty => 'இன்னும் பதிவுகள் இல்லை';

  @override
  String get diaryAdd => 'பதிவு சேர்';

  @override
  String get diaryKindNote => 'குறிப்பு';

  @override
  String get diaryKindObservation => 'கவனிப்பு';

  @override
  String get diaryKindExpense => 'செலவு';

  @override
  String get diaryKindIncome => 'வருமானம்';

  @override
  String get diaryKindQuestion => 'கேள்வி';

  @override
  String get diaryKindScan => 'ஸ்கேன்';

  @override
  String get diaryHistory => 'வரலாறு';

  @override
  String get diaryText => 'விவரம்';

  @override
  String get diaryTextRequired => 'விவரத்தை உள்ளிடவும்';

  @override
  String get diaryAmount => 'தொகை (ரூ)';

  @override
  String get diaryAmountInvalid => 'சரியான தொகையை உள்ளிடவும்';

  @override
  String get diaryDate => 'நாள்';

  @override
  String get satelliteUnavailable => 'செயற்கைக்கோள் நிலை தற்போது கிடைக்கவில்லை';

  @override
  String get satelliteUnderValidation =>
      'செயற்கைக்கோள் நுண்ணறிவு சரிபார்ப்பில் உள்ளது';

  @override
  String get satelliteAvailable => 'செயற்கைக்கோள் நுண்ணறிவு கிடைக்கிறது';

  @override
  String get satelliteNoPredictions =>
      'அனைத்துச் சரிபார்ப்புகளும் முடியும் வரை படங்களோ கணிப்புகளோ காட்டப்படாது.';

  @override
  String get satelliteGates => 'சரிபார்ப்பு நிலைகள்';

  @override
  String get gateLicence => 'தரவு உரிமம்';

  @override
  String get gateUnits => 'அலகுகள் சரிபார்ப்பு';

  @override
  String get gateGeography => 'புவியியல் வரம்பு';

  @override
  String get gateEvaluation => 'சுயாதீன மதிப்பீடு';

  @override
  String get gatePassed => 'முடிந்தது';

  @override
  String get gateNotPassed => 'இன்னும் முடியவில்லை';

  @override
  String get assistantUnavailable => 'உதவியாளர் சேவை தற்போது கிடைக்கவில்லை';

  @override
  String get assistantError =>
      'பதிலைப் பெற முடியவில்லை. மீண்டும் முயற்சிக்கவும்.';

  @override
  String get assistantIntro =>
      'பயிர், வானிலை, திட்டங்கள் பற்றி தமிழிலோ ஆங்கிலத்திலோ கேளுங்கள்.';

  @override
  String get assistantSuggestions => 'இவற்றில் ஒன்றைக் கேட்கலாம்:';

  @override
  String get assistantHint => 'உங்கள் கேள்வியை எழுதுங்கள்';

  @override
  String get assistantSend => 'அனுப்பு';

  @override
  String get assistantNewChat => 'புதிய உரையாடல்';

  @override
  String get assistantSources => 'ஆதாரங்கள்';

  @override
  String get assistantFallbackNote =>
      'இந்தப் பதிலுக்குச் சரிபார்க்கப்பட்ட ஆதாரம் கிடைக்கவில்லை. வேளாண் அலுவலரிடம் உறுதி செய்யவும்.';

  @override
  String get suggest1 => 'நெல் நாற்றங்காலை எப்படித் தயாரிப்பது?';

  @override
  String get suggest2 => 'இந்த வாரம் மழை பெய்யுமா?';

  @override
  String get suggest3 => 'எனக்குப் பொருந்தும் அரசு திட்டங்கள் எவை?';

  @override
  String get suggest4 => 'மண் பரிசோதனை ஏன் செய்ய வேண்டும்?';

  @override
  String get stageStarting => 'தொடங்குகிறது…';

  @override
  String get stageUnderstanding => 'கேள்வியைப் புரிந்துகொள்கிறது…';

  @override
  String get stagePlanning => 'திட்டமிடுகிறது…';

  @override
  String get stageGathering => 'தகவல் சேகரிக்கிறது…';

  @override
  String get stageEvidence => 'ஆதாரங்களைச் சரிபார்க்கிறது…';

  @override
  String get stageGrounding => 'ஆதாரங்களுடன் ஒப்பிடுகிறது…';

  @override
  String get stageWriting => 'பதில் எழுதுகிறது…';

  @override
  String get voiceStart => 'குரலில் கேளுங்கள்';

  @override
  String get voiceStop => 'நிறுத்து';

  @override
  String get voiceListening => 'கேட்கிறது…';

  @override
  String get voiceThinking => 'சிந்திக்கிறது…';

  @override
  String get voiceSpeaking => 'பதில் கூறுகிறது…';

  @override
  String get voiceModeOn => 'குரல் உரையாடல் முறை ஆன்';

  @override
  String get voiceModeOff => 'குரல் உரையாடல் முறை ஆஃப்';

  @override
  String get voicePermissionDenied =>
      'மைக்ரோஃபோன் அனுமதி இல்லை. அமைப்புகளில் அனுமதி தரவும்.';

  @override
  String get voiceNotAvailable =>
      'இந்தக் கைபேசியில் குரல் உள்ளீடு கிடைக்கவில்லை';

  @override
  String get speakAnswer => 'பதிலைக் கேளுங்கள்';

  @override
  String get ttsNotAvailable => 'இந்த மொழிக்கு குரல் வாசிப்பு கிடைக்கவில்லை';

  @override
  String get scanCrop => 'பயிர்';

  @override
  String get scanPaddyExcluded => 'நெல்லுக்கான ஸ்கேன் தற்போது இல்லை';

  @override
  String get scanCamera => 'படம் எடு';

  @override
  String get scanGallery => 'கேலரியிலிருந்து';

  @override
  String get scanYourPhoto => 'நீங்கள் எடுத்த படம்';

  @override
  String get scanRetake => 'மீண்டும் எடு';

  @override
  String get scanRemove => 'நீக்கு';

  @override
  String get scanSubmit => 'பரிசோதனைக்கு அனுப்பு';

  @override
  String get scanPickCropFirst => 'முதலில் பயிரைத் தேர்ந்தெடுக்கவும்';

  @override
  String get scanUploading => 'பதிவேற்றுகிறது…';

  @override
  String scanUploadingPct(int pct) {
    return 'பதிவேற்றுகிறது… $pct%';
  }

  @override
  String get scanModelUnavailable =>
      'சரிபார்க்கப்பட்ட நோய் கண்டறியும் மாதிரி இன்னும் கிடைக்கவில்லை. உள்ளூர் வேளாண் அலுவலரை அணுகவும்.';

  @override
  String get scanUnsure =>
      'உறுதியாகச் சொல்ல முடியவில்லை. வேளாண் அலுவலரை அணுகவும்.';

  @override
  String get scanImageTooLarge =>
      'படம் மிகப் பெரியது. சிறிய படத்தை முயற்சிக்கவும்.';

  @override
  String get scanUnsupportedImage =>
      'இந்தப் படத்தைப் பயன்படுத்த முடியாது. JPEG, PNG அல்லது WebP படத்தை முயற்சிக்கவும்.';

  @override
  String get scanPickFailed => 'படத்தைப் பெற முடியவில்லை';

  @override
  String get cameraPermissionDenied =>
      'கேமரா அனுமதி இல்லை. அமைப்புகளில் அனுமதி தரவும்.';

  @override
  String get galleryPermissionDenied => 'படங்களை அணுக அனுமதி இல்லை';

  @override
  String get scanResultTitle => 'மாதிரியின் முடிவு';

  @override
  String get scanProbability => 'நிகழ்தகவு';

  @override
  String get scanModelVersion => 'மாதிரிப் பதிப்பு';

  @override
  String get scanInferredAt => 'கணித்த நேரம்';

  @override
  String get scanGuidance => 'வழிகாட்டுதல்';

  @override
  String get scanConfirmWithOfficer =>
      'நடவடிக்கைக்கு முன் வேளாண் அலுவலரிடம் உறுதி செய்யவும்.';

  @override
  String get errValueOutOfRange =>
      'ஒரு மதிப்பு அனுமதிக்கப்பட்ட வரம்பிற்கு வெளியே உள்ளது. சரிபார்க்கவும்.';

  @override
  String get weatherIssuedNotProvided =>
      'முன்னறிவிப்பு வெளியான நேரம் வழங்கப்படவில்லை';

  @override
  String weatherIssuedAt(String time) {
    return 'முன்னறிவிப்பு வெளியானது $time';
  }

  @override
  String get marketVariety => 'ரகம்';

  @override
  String marketVarietyValue(String variety) {
    return 'ரகம்: $variety';
  }

  @override
  String get schemeStatus => 'நிலை (மூலத்தில்)';

  @override
  String get schemeActiveOnSource => 'மூலத்தில் செயலில் உள்ளது';

  @override
  String get schemeStatusNotStated => 'மூலத்தில் நிலை குறிப்பிடப்படவில்லை';

  @override
  String get schemeComponents => 'திட்டக் கூறுகள்';

  @override
  String get eligibilitySignIn => 'தகுதியைச் சரிபார்க்க மீண்டும் உள்நுழையவும்';

  @override
  String get soilSurvey => 'ஆய்வு';

  @override
  String get soilCycle => 'சுழற்சி';

  @override
  String soilParamSamples(String param, int samples) {
    return '$param ($samples மாதிரிகள்)';
  }

  @override
  String get soilLow => 'குறைவு';

  @override
  String get soilMedium => 'நடுத்தரம்';

  @override
  String get soilHigh => 'அதிகம்';

  @override
  String homeGreeting(String name) {
    return 'வணக்கம், $name';
  }

  @override
  String get homeGreetingNoName => 'வணக்கம்';

  @override
  String get homeNoFarm => 'இன்னும் பண்ணை சேர்க்கப்படவில்லை';

  @override
  String get homeSetCrop =>
      'சந்தை விலைகளைப் பொருத்த, பண்ணையில் பயிரை அமைக்கவும்';

  @override
  String get homeMarketSnapshot => 'சந்தை விலைகள் (சமீபத்திய பதிவு)';

  @override
  String get homeMarketNeedsFarm =>
      'சந்தை விலைகளைக் காண பண்ணை அல்லது மாவட்டத்தை அமைக்கவும்';

  @override
  String get homeRecentActivity => 'சமீபத்திய செயல்பாடு';

  @override
  String get homeShortcuts => 'விரைவு அணுகல்';

  @override
  String get homeSeeAll => 'அனைத்தும்';

  @override
  String soilSamplesCount(int count) {
    return '$count மாதிரிகள்';
  }

  @override
  String get homeNoMarketForCrop =>
      'இந்தப் பயிருக்குச் சந்தை விலைத் தரவு இல்லை';

  @override
  String get voiceOfflineUnavailable =>
      'இந்தக் கைபேசியில் ஆஃப்லைன் குரல் அறிதல் இல்லை. எனவே எதுவும் பதிவு செய்யப்படவில்லை, பதிவேற்றப்படவில்லை. கேள்வியை தட்டச்சு செய்யவும்.';

  @override
  String get voiceOfflineLanguageMissing =>
      'இந்த மொழிக்கான ஆஃப்லைன் பேச்சுத் தொகுப்பு நிறுவப்படவில்லை. கைபேசியின் பேச்சு அமைப்புகளில் நிறுவவும் (எ.கா. Google ஆப் > Settings > Voice > Offline speech recognition). அதுவரை கேள்வியை தட்டச்சு செய்யலாம்.';

  @override
  String get voiceTtsMissingTamil =>
      'ஆஃப்லைன் தமிழ் குரல் நிறுவப்படவில்லை, அதனால் பதிலை வாசிக்க முடியவில்லை. நிறுவ: Settings > General management > Text-to-speech output > engine settings > Install voice data > Tamil.';

  @override
  String get voiceTtsMissingEnglish =>
      'ஆஃப்லைன் ஆங்கிலக் குரல் நிறுவப்படவில்லை, அதனால் பதிலை வாசிக்க முடியவில்லை. நிறுவ: Settings > General management > Text-to-speech output > engine settings > Install voice data.';

  @override
  String get voiceTtsFailed =>
      'பதிலை வாசிக்க முடியவில்லை. ஒலிபெருக்கி படத்தைத் தட்டி மீண்டும் முயற்சிக்கவும்.';

  @override
  String get voiceSttError =>
      'குரல் உள்ளீடு எதிர்பாராமல் நின்றது. மீண்டும் முயற்சிக்கவும் அல்லது தட்டச்சு செய்யவும்.';

  @override
  String get voiceDismiss => 'மூடு';

  @override
  String get brandTagline =>
      'தமிழ்நாட்டு விவசாயிகளுக்கான வழிகாட்டுதல், தமிழிலும் ஆங்கிலத்திலும்';

  @override
  String get loginPhoneHelp =>
      'இந்த எண்ணுக்கு ஒருமுறை குறியீடு அனுப்பப்படும். கடவுச்சொல் தேவையில்லை.';

  @override
  String get homeFarmLabel => 'உங்கள் நிலம்';

  @override
  String get homeAskTitle => 'வேளாண் உதவியாளரிடம் கேளுங்கள்';

  @override
  String get homeAskSubtitle =>
      'பயிர், மண், வானிலை, திட்டங்கள். ஆதாரங்கள் கிடைத்தால் காட்டப்படும்.';

  @override
  String get homeAskAction => 'கேள்வி கேளுங்கள்';

  @override
  String get homeServices => 'சேவைகள்';

  @override
  String get moreInfoSection => 'விவசாயத் தகவல்';

  @override
  String get moreRecordsSection => 'உங்கள் பதிவுகள்';

  @override
  String get moreAccountSection => 'கணக்கு';

  @override
  String get moreWeatherSub => 'தற்போதைய நிலை மற்றும் 7 நாள் முன்னறிவிப்பு';

  @override
  String get moreMarketSub => 'பதிவான விலைகள்; நேரடி விலை அல்ல';

  @override
  String get moreSchemesSub => 'மத்திய, மாநில திட்டங்கள்';

  @override
  String get moreSoilSub => 'பகுதி மண் தகவல் மற்றும் உங்கள் மண் பரிசோதனைகள்';

  @override
  String get moreScanSub =>
      'சரிபார்ப்பில் உள்ளது; நோய் கண்டறிதல் இன்னும் இல்லை';

  @override
  String get moreFarmsSub => 'நிலங்களைச் சேர்க்க அல்லது திருத்த';

  @override
  String get moreDiarySub => 'குறிப்புகள் மற்றும் பண்ணை நடவடிக்கைகள்';

  @override
  String get moreSatelliteSub => 'செயற்கைக்கோள் வசதிகளின் நிலை';

  @override
  String get moreProfileSub => 'பெயர், மாவட்டம், மொழி';

  @override
  String get moreSettingsSub => 'மொழி, தோற்றம், பற்றி';

  @override
  String get assistantEmptyTitle => 'உங்கள் விவசாயத்திற்கு எப்படி உதவலாம்?';

  @override
  String get assistantCopy => 'பதிலை நகலெடு';

  @override
  String get assistantCopied => 'பதில் நகலெடுக்கப்பட்டது';

  @override
  String get assistantGeneralGuidance => 'பொது வழிகாட்டுதல்';

  @override
  String get assistantGeneralGuidanceNote => 'TNAU ஆதாரம் இல்லாமல்';

  @override
  String get assistantSourcesNote =>
      'இந்தப் பதிலுக்காகப் பெறப்பட்ட ஆவணங்கள். ஒவ்வொரு வாக்கியத்தையும் இவை உறுதிப்படுத்தாமல் இருக்கலாம்.';

  @override
  String get assistantNoAnswerTitle => 'சரிபார்க்கப்பட்ட பதில் இல்லை';

  @override
  String get voiceTapToStop => 'நிறுத்த தட்டவும்';

  @override
  String get voiceSpeakAnswer => 'கேளுங்கள்';

  @override
  String get scanValidationBadge => 'சரிபார்ப்பில் உள்ளது';

  @override
  String get scanValidationTitle => 'நோய் கண்டறிதல் இன்னும் கிடைக்கவில்லை';

  @override
  String get scanValidationBody =>
      'நோய் மாதிரி விவசாயிகள் பயன்பாட்டிற்கு இன்னும் அங்கீகரிக்கப்படவில்லை. நீங்கள் அனுப்பும் புகைப்படத்திற்கு நோய் கண்டறிதல் வழங்கப்படாது. பயிர் பிரச்சனைக்கு உங்கள் பகுதி வேளாண் அலுவலரை அணுகவும்.';

  @override
  String get scanHowTitle => 'இங்கே என்ன செய்யலாம்';

  @override
  String get scanHowBody =>
      'பயிரையும் பாதிக்கப்பட்ட இலையின் தெளிவான புகைப்படத்தையும் தேர்ந்தெடுக்கவும். சரிபார்க்கப்பட்ட முடிவு கிடைக்குமா என்பதை ஆப் நேர்மையாகத் தெரிவிக்கும்.';

  @override
  String get marketSnapshotBadge => 'பதிவான விலை; நேரடி அல்ல';

  @override
  String get settingsAppearance => 'தோற்றம்';

  @override
  String get settingsPrivacy => 'தனியுரிமை';

  @override
  String get settingsPrivacyBody =>
      'உங்கள் கேள்விகளுக்கு UZHAVAN சேவையகத்தில் இயங்கும் மாதிரி பதிலளிக்கிறது; கட்டண மேகக்கணி AI சேவை பயன்படுத்தப்படவில்லை. பேச்சு இந்தக் கைபேசியின் சொந்தக் குரலில் உருவாகிறது. வானிலை Open-Meteo-விலிருந்து, உங்கள் மாவட்ட இருப்பிடத்தை மட்டும் பயன்படுத்திப் பெறப்படுகிறது.';

  @override
  String get settingsVoice => 'குரல்';

  @override
  String get settingsVoiceBody =>
      'பதில்கள் இந்தக் கைபேசியின் குரலில் வாசிக்கப்படும். குரல் உள்ளீட்டிற்கு Android 12 அல்லது புதியதும் ஆஃப்லைன் மொழித் தொகுப்பும் தேவை; இல்லையெனில் கேள்வியைத் தட்டச்சு செய்யவும்.';
}
