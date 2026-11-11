// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'UZHAVAN AI';

  @override
  String get languageSwitchLabel => 'English → தமிழ்';

  @override
  String get languageSwitchTooltip => 'Change language';

  @override
  String get languageTamil => 'தமிழ்';

  @override
  String get languageEnglish => 'English';

  @override
  String get notSet => 'Not set';

  @override
  String get optionalSuffix => '(optional)';

  @override
  String get retry => 'Retry';

  @override
  String get loading => 'Loading…';

  @override
  String get stateError => 'Something went wrong';

  @override
  String get stateUnsure => 'Not sure: please consult an agricultural officer';

  @override
  String get stateUnavailable => 'This service is not available right now';

  @override
  String get stateEmpty => 'Nothing to show yet';

  @override
  String get comingSoon => 'This feature is coming in a later update';

  @override
  String get navHome => 'Home';

  @override
  String get navAssistant => 'Assistant';

  @override
  String get navScan => 'Scan';

  @override
  String get navMarket => 'Market';

  @override
  String get navMore => 'More';

  @override
  String get featureHome => 'Home';

  @override
  String get featureAssistant => 'Farming assistant';

  @override
  String get featureScan => 'Crop disease scan';

  @override
  String get featureMarket => 'Market prices';

  @override
  String get featureWeather => 'Weather';

  @override
  String get featureSchemes => 'Government schemes';

  @override
  String get featureSoil => 'Soil';

  @override
  String get featureFarms => 'My farms';

  @override
  String get featureDiary => 'Farm diary';

  @override
  String get featureSatellite => 'Satellite';

  @override
  String get featureProfile => 'Profile';

  @override
  String get featureSettings => 'Settings';

  @override
  String get back => 'Back';

  @override
  String get loginTitle => 'Sign in';

  @override
  String get loginSubtitle => 'Enter your phone number';

  @override
  String get phoneLabel => 'Phone number';

  @override
  String get phonePrefix => '+91';

  @override
  String get phoneHint => '10-digit number';

  @override
  String get phoneInvalid =>
      'Enter a 10-digit number starting with 6, 7, 8 or 9';

  @override
  String get sendOtp => 'Send OTP';

  @override
  String get otpTitle => 'Verify your phone';

  @override
  String otpSentTo(String phone) {
    return 'OTP sent to +91 $phone';
  }

  @override
  String get otpLabel => '6-digit OTP';

  @override
  String get otpInvalid => 'Enter the 6-digit code';

  @override
  String get verify => 'Verify';

  @override
  String get resendOtp => 'Resend code';

  @override
  String resendIn(int seconds) {
    return 'Resend in $seconds s';
  }

  @override
  String get changeNumber => 'Change number';

  @override
  String get otpResent => 'A new code has been sent';

  @override
  String get errOtpIncorrect => 'Incorrect code. Please try again.';

  @override
  String get errOtpExpired => 'The code has expired. Request a new one.';

  @override
  String get errOtpAttemptsExceeded =>
      'Too many wrong attempts. Request a new code.';

  @override
  String get errOtpNotFound => 'No active code. Request a new one.';

  @override
  String get errRateLimited => 'Too many requests. Please try again later.';

  @override
  String errRateLimitedSeconds(int seconds) {
    return 'Too many requests. Try again in $seconds s.';
  }

  @override
  String errRateLimitedMinutes(int minutes) {
    return 'Too many requests. Try again in $minutes min.';
  }

  @override
  String get errOtpDeliveryNotConfigured =>
      'SMS delivery is not available right now. Please try later.';

  @override
  String get errServerUnreachable => 'Can\'t reach the UZHAVAN server';

  @override
  String get errSessionExpired =>
      'Your session has ended. Please sign in again.';

  @override
  String get errValidation => 'Please check the details you entered';

  @override
  String get errNotFound => 'The requested item was not found';

  @override
  String get profileName => 'Name';

  @override
  String get profileDistrict => 'District';

  @override
  String get profileVillage => 'Village';

  @override
  String get profilePhone => 'Phone';

  @override
  String get profileLanguage => 'Preferred language';

  @override
  String get profileEdit => 'Edit profile';

  @override
  String get profileUnavailable => 'Profile data unavailable';

  @override
  String get profileStillIncomplete =>
      'Your profile is still incomplete. Please fill in the required details.';

  @override
  String get onboardingTitle => 'Your details';

  @override
  String get onboardingSubtitle => 'Helps us give better advice';

  @override
  String get onboardingContinue => 'Continue';

  @override
  String get nameInvalid => 'Name must be 2 to 100 characters';

  @override
  String get districtRequired => 'Select a district';

  @override
  String get districtPickerTitle => 'Select your district';

  @override
  String get searchHint => 'Search';

  @override
  String get districtsUnavailable => 'District list unavailable';

  @override
  String get optionsUnavailable => 'Options list unavailable';

  @override
  String get noMatches => 'No matches';

  @override
  String get pickerNone => 'None selected';

  @override
  String get save => 'Save';

  @override
  String get cancel => 'Cancel';

  @override
  String get saved => 'Saved';

  @override
  String get delete => 'Delete';

  @override
  String get edit => 'Edit';

  @override
  String get logout => 'Log out';

  @override
  String get logoutConfirm => 'Log out of UZHAVAN AI?';

  @override
  String get farmAdd => 'Add farm';

  @override
  String get farmEdit => 'Edit farm';

  @override
  String farmDeleteConfirm(String name) {
    return 'Delete the farm \"$name\"?';
  }

  @override
  String get farmDeleted => 'Farm deleted';

  @override
  String get farmsEmpty => 'No farms added yet';

  @override
  String get farmsUnavailable => 'Farm data unavailable';

  @override
  String get farmName => 'Farm name';

  @override
  String get farmNameRequired => 'Enter a farm name';

  @override
  String get farmLocation => 'Location';

  @override
  String get farmLocationHelp =>
      'Enter both latitude and longitude, or leave both empty';

  @override
  String get farmLatitude => 'Latitude';

  @override
  String get farmLongitude => 'Longitude';

  @override
  String get farmLatInvalid =>
      'Latitude must be between 8.0 and 13.6 (Tamil Nadu)';

  @override
  String get farmLonInvalid =>
      'Longitude must be between 76.2 and 80.4 (Tamil Nadu)';

  @override
  String get farmLatLonPair => 'Enter both latitude and longitude';

  @override
  String farmCoordinatesValue(String lat, String lon) {
    return '$lat, $lon';
  }

  @override
  String get farmArea => 'Land size (acres)';

  @override
  String get farmAreaInvalid => 'Enter a valid area in acres';

  @override
  String farmAreaValue(String acres) {
    return '$acres acres';
  }

  @override
  String get farmCrop => 'Crop';

  @override
  String get farmStage => 'Crop stage';

  @override
  String get farmSeason => 'Season';

  @override
  String get farmIrrigation => 'Irrigation';

  @override
  String get settingsLanguage => 'Language';

  @override
  String get settingsTheme => 'Theme';

  @override
  String get themeLight => 'Light';

  @override
  String get themeDark => 'Dark';

  @override
  String get themeSystem => 'System default';

  @override
  String get settingsAbout => 'About';

  @override
  String get aboutDescription => 'Farming assistant for Tamil Nadu farmers';

  @override
  String appVersion(String version) {
    return 'Version $version';
  }

  @override
  String apiBaseUrlDebug(String url) {
    return 'API address (debug): $url';
  }

  @override
  String get configErrorTitle => 'Configuration error';

  @override
  String get configErrorInsecure =>
      'This release build needs a secure (https) API address.';

  @override
  String get configErrorInvalid => 'The API address is invalid.';

  @override
  String configErrorDetail(String url) {
    return 'API_BASE_URL: $url';
  }

  @override
  String get farmLimitReached => 'You can add up to 5 farms';

  @override
  String get errInvalidDistrict => 'The selected district is not valid';

  @override
  String get errInvalidLanguage => 'The selected language is not valid';

  @override
  String get errInvalidVillage => 'Please check the village name';

  @override
  String get errInvalidLocation => 'The location values are not valid';

  @override
  String get errLocationOutsideTn => 'The location must be inside Tamil Nadu';

  @override
  String get errInvalidBoundary => 'The farm boundary is not valid';

  @override
  String get errInvalidCrop => 'The selected crop is not valid';

  @override
  String get errInvalidCropStage => 'The selected crop stage is not valid';

  @override
  String get errInvalidSeason => 'The selected season is not valid';

  @override
  String get errInvalidIrrigationType =>
      'The selected irrigation type is not valid';

  @override
  String get notAvailable => 'Not available';

  @override
  String sourceLabel(String source) {
    return 'Source: $source';
  }

  @override
  String updatedAt(String time) {
    return 'Updated $time';
  }

  @override
  String observedOn(String date) {
    return 'Observed on $date';
  }

  @override
  String get oldData => 'Old data';

  @override
  String get kindCurrent => 'Current';

  @override
  String get kindForecast => 'Forecast';

  @override
  String get kindHistorical => 'Historical';

  @override
  String get kindLatestObserved => 'Latest observed';

  @override
  String get kindEstimated => 'Estimated (model)';

  @override
  String get kindMeasured => 'Measured';

  @override
  String get kindReference => 'Reference';

  @override
  String get linkOpenFailed => 'Could not open the link';

  @override
  String get farmPickerLabel => 'Farm';

  @override
  String get locationMissing =>
      'Add a farm or set your district in the profile';

  @override
  String get close => 'Close';

  @override
  String get weatherUnavailable => 'Weather data is not available right now';

  @override
  String get weatherNow => 'Current weather';

  @override
  String weatherLocation(String name) {
    return 'Location: $name';
  }

  @override
  String get weatherFeelsLike => 'Feels like';

  @override
  String get weatherHumidity => 'Humidity';

  @override
  String get weatherRain => 'Rain';

  @override
  String get weatherWind => 'Wind';

  @override
  String get weatherModelTime => 'Model time';

  @override
  String get weatherForecast7 => '7-day forecast';

  @override
  String get weatherToday => 'Today\'s forecast';

  @override
  String get weatherForecastEmpty => 'No forecast data';

  @override
  String weatherMaxMin(String max, String min) {
    return 'Max $max · Min $min';
  }

  @override
  String weatherRainLine(String mm, String pct) {
    return 'Rain $mm · Chance $pct';
  }

  @override
  String get weatherAdvisories => 'Weather advisories';

  @override
  String get weatherNoAdvisories => 'No advisory rule applies right now';

  @override
  String get severityCaution => 'Caution';

  @override
  String get severityInfo => 'Info';

  @override
  String ruleSource(String source) {
    return 'Rule source: $source';
  }

  @override
  String get marketUnavailable => 'Market data is not available right now';

  @override
  String get marketEmpty => 'No price observations for this selection';

  @override
  String get marketDistrictFilter => 'District';

  @override
  String get allCommodities => 'All';

  @override
  String get marketLatestTitle => 'Latest observed prices';

  @override
  String get marketTapForTrend => 'Tap a row to see its historical price trend';

  @override
  String marketMinMax(String min, String max) {
    return 'Min ₹ $min – Max ₹ $max';
  }

  @override
  String get unitRsPerQuintal => 'Rs/quintal';

  @override
  String unitNoteLabel(String note) {
    return 'Unit note: $note';
  }

  @override
  String get marketTrend => 'Price trend (historical)';

  @override
  String marketTrendTitle(String name) {
    return '$name: historical price trend';
  }

  @override
  String marketTrendCaption(String market, int days) {
    return '$market · last $days days · modal price';
  }

  @override
  String get marketTrendEmpty => 'No historical prices for this market';

  @override
  String get schemesUnavailable => 'Scheme data is not available right now';

  @override
  String get schemesEmpty => 'No schemes match this search';

  @override
  String get schemeSearchHint => 'Search schemes';

  @override
  String get levelAll => 'All';

  @override
  String get levelCentral => 'Central';

  @override
  String get levelState => 'State';

  @override
  String get schemeCropFilter => 'Crop';

  @override
  String schemesCount(int count) {
    return '$count schemes';
  }

  @override
  String get schemeInactive => 'Inactive on source';

  @override
  String get schemeLevel => 'Level';

  @override
  String get schemeAuthority => 'Authority';

  @override
  String get schemeDateChecked => 'Date checked';

  @override
  String get schemeLastUpdatedOnSource => 'Last updated on source';

  @override
  String get schemeOfficialLink => 'Official page';

  @override
  String get schemeDescription => 'Description';

  @override
  String get schemeEligibilityText => 'Eligibility (official text)';

  @override
  String get schemeBenefits => 'Benefits';

  @override
  String get schemeHowToApply => 'How to apply';

  @override
  String get schemeDocuments => 'Required documents';

  @override
  String get schemeSourceDocuments => 'Source documents';

  @override
  String get eligibilityTitle => 'Your eligibility check';

  @override
  String get eligibilityUnavailable =>
      'The eligibility check is not available right now';

  @override
  String get eligMeetsKnown => 'You meet the known criteria';

  @override
  String get eligFailsKnown => 'You do not meet the known criteria';

  @override
  String get eligMoreInfo => 'More information required';

  @override
  String get eligCannotDetermine => 'Cannot determine';

  @override
  String get eligibilityNoResult => 'No eligibility result available';

  @override
  String get eligibilityReasons => 'Reasons';

  @override
  String get eligibilityMissing => 'Details needed';

  @override
  String get eligibilityCriteriaSource => 'Criteria source';

  @override
  String get eligibilityDisclaimer =>
      'This checks only the known criteria; the final decision rests with the government office.';

  @override
  String get soilUnavailable => 'Soil data is not available right now';

  @override
  String get soilRegionalTitle => 'Regional information';

  @override
  String get soilTypes => 'Soil types in this area';

  @override
  String get soilNutrientStatus => 'District nutrient status';

  @override
  String get soilNutrientStatusCaption => 'Share of samples in each category';

  @override
  String get soilEstimatedTitle => 'Estimated (model) values';

  @override
  String get soilEstimatedWarning =>
      'These are model estimates, not measurements of your field';

  @override
  String get soilDepth => 'Depth';

  @override
  String get soilMeasuredTitle => 'Your soil tests (measured)';

  @override
  String get soilNoTests => 'No soil test results added yet';

  @override
  String get soilAddTest => 'Add soil test';

  @override
  String get soilAddTestNeedsFarm => 'Add a farm first to record a soil test';

  @override
  String soilSampleOn(String date) {
    return 'Sampled on $date';
  }

  @override
  String soilLab(String lab) {
    return 'Lab: $lab';
  }

  @override
  String get soilFarmerEntered => 'Entered by you';

  @override
  String get soilSampleDate => 'Sample date';

  @override
  String get soilPickDate => 'Pick a date';

  @override
  String get soilLabName => 'Lab name';

  @override
  String get soilValuesHint =>
      'Enter only the values printed on your soil test report; leave the rest empty.';

  @override
  String get soilValueInvalid => 'Enter a valid number';

  @override
  String soilValueRange(String min, String max) {
    return 'Allowed: $min – $max';
  }

  @override
  String get soilFarmRequired => 'Choose a farm';

  @override
  String get soilDateRequired => 'Choose the sample date';

  @override
  String get soilAtLeastOne => 'Enter at least one value';

  @override
  String get soilPh => 'pH';

  @override
  String get soilSoc => 'Soil organic carbon';

  @override
  String get soilClay => 'Clay';

  @override
  String get soilSand => 'Sand';

  @override
  String get soilSilt => 'Silt';

  @override
  String get soilCec => 'Cation exchange capacity (CEC)';

  @override
  String get soilBdod => 'Bulk density';

  @override
  String get soilNitrogenEst => 'Total nitrogen';

  @override
  String get soilEc => 'Electrical conductivity (EC)';

  @override
  String get soilOc => 'Organic carbon (OC)';

  @override
  String get soilN => 'Nitrogen (N)';

  @override
  String get soilP => 'Phosphorus (P)';

  @override
  String get soilK => 'Potassium (K)';

  @override
  String get soilS => 'Sulphur (S)';

  @override
  String get soilZn => 'Zinc (Zn)';

  @override
  String get soilFe => 'Iron (Fe)';

  @override
  String get soilCu => 'Copper (Cu)';

  @override
  String get soilMn => 'Manganese (Mn)';

  @override
  String get soilB => 'Boron (B)';

  @override
  String get diaryUnavailable => 'The diary is not available right now';

  @override
  String get diaryEmpty => 'No entries yet';

  @override
  String get diaryAdd => 'Add entry';

  @override
  String get diaryKindNote => 'Note';

  @override
  String get diaryKindObservation => 'Observation';

  @override
  String get diaryKindExpense => 'Expense';

  @override
  String get diaryKindIncome => 'Income';

  @override
  String get diaryKindQuestion => 'Question';

  @override
  String get diaryKindScan => 'Scan';

  @override
  String get diaryHistory => 'History';

  @override
  String get diaryText => 'Details';

  @override
  String get diaryTextRequired => 'Enter the details';

  @override
  String get diaryAmount => 'Amount (Rs)';

  @override
  String get diaryAmountInvalid => 'Enter a valid amount';

  @override
  String get diaryDate => 'Date';

  @override
  String get satelliteUnavailable =>
      'Satellite status is not available right now';

  @override
  String get satelliteUnderValidation =>
      'Satellite intelligence under validation';

  @override
  String get satelliteAvailable => 'Satellite intelligence is available';

  @override
  String get satelliteNoPredictions =>
      'No imagery or predictions are shown until every check below has passed.';

  @override
  String get satelliteGates => 'Validation gates';

  @override
  String get gateLicence => 'Data licence';

  @override
  String get gateUnits => 'Units verified';

  @override
  String get gateGeography => 'Geographic scope';

  @override
  String get gateEvaluation => 'Independent evaluation';

  @override
  String get gatePassed => 'Passed';

  @override
  String get gateNotPassed => 'Not passed yet';

  @override
  String get assistantUnavailable => 'The assistant is not available right now';

  @override
  String get assistantError => 'Could not get an answer. Please try again.';

  @override
  String get assistantIntro =>
      'Ask about crops, weather or schemes in Tamil or English.';

  @override
  String get assistantSuggestions => 'You could ask:';

  @override
  String get assistantHint => 'Type your question';

  @override
  String get assistantSend => 'Send';

  @override
  String get assistantNewChat => 'New conversation';

  @override
  String get assistantSources => 'Sources';

  @override
  String get assistantFallbackNote =>
      'No verified source was found for this answer. Please confirm with an agricultural officer.';

  @override
  String get suggest1 => 'How do I prepare a paddy nursery?';

  @override
  String get suggest2 => 'Will it rain this week?';

  @override
  String get suggest3 => 'Which government schemes apply to me?';

  @override
  String get suggest4 => 'Why should I test my soil?';

  @override
  String get stageStarting => 'Starting…';

  @override
  String get stageUnderstanding => 'Understanding your question…';

  @override
  String get stagePlanning => 'Planning…';

  @override
  String get stageGathering => 'Gathering information…';

  @override
  String get stageEvidence => 'Checking the evidence…';

  @override
  String get stageGrounding => 'Verifying against sources…';

  @override
  String get stageWriting => 'Writing the answer…';

  @override
  String get voiceStart => 'Ask by voice';

  @override
  String get voiceStop => 'Stop';

  @override
  String get voiceListening => 'Listening…';

  @override
  String get voiceThinking => 'Thinking…';

  @override
  String get voiceSpeaking => 'Speaking…';

  @override
  String get voiceModeOn => 'Voice Conversation Mode: ON';

  @override
  String get voiceModeOff => 'Voice Conversation Mode: OFF';

  @override
  String get voicePermissionDenied =>
      'Microphone permission denied. Allow it in the phone settings.';

  @override
  String get voiceNotAvailable => 'Voice input is not available on this phone';

  @override
  String get speakAnswer => 'Listen to the answer';

  @override
  String get ttsNotAvailable => 'Read-aloud is not available for this language';

  @override
  String get scanCrop => 'Crop';

  @override
  String get scanPaddyExcluded => 'Paddy scanning is not offered yet';

  @override
  String get scanCamera => 'Take photo';

  @override
  String get scanGallery => 'From gallery';

  @override
  String get scanYourPhoto => 'Your photo';

  @override
  String get scanRetake => 'Retake';

  @override
  String get scanRemove => 'Remove';

  @override
  String get scanSubmit => 'Send for checking';

  @override
  String get scanPickCropFirst => 'Choose the crop first';

  @override
  String get scanUploading => 'Uploading…';

  @override
  String scanUploadingPct(int pct) {
    return 'Uploading… $pct%';
  }

  @override
  String get scanModelUnavailable =>
      'Validated disease model unavailable. Please contact your local agricultural officer.';

  @override
  String get scanUnsure => 'Not sure. Please consult an agricultural officer.';

  @override
  String get scanImageTooLarge =>
      'The image is too large. Try a smaller photo.';

  @override
  String get scanUnsupportedImage =>
      'This image can\'t be used. Try a JPEG, PNG or WebP photo.';

  @override
  String get scanPickFailed => 'Could not get the photo';

  @override
  String get cameraPermissionDenied =>
      'Camera permission denied. Allow it in the phone settings.';

  @override
  String get galleryPermissionDenied => 'Photo access denied';

  @override
  String get scanResultTitle => 'Model result';

  @override
  String get scanProbability => 'Probability';

  @override
  String get scanModelVersion => 'Model version';

  @override
  String get scanInferredAt => 'Checked at';

  @override
  String get scanGuidance => 'Guidance';

  @override
  String get scanConfirmWithOfficer =>
      'Confirm with an agricultural officer before acting.';

  @override
  String get errValueOutOfRange =>
      'A value is outside the allowed range. Please check it.';

  @override
  String get weatherIssuedNotProvided => 'Issued time not provided';

  @override
  String weatherIssuedAt(String time) {
    return 'Issued $time';
  }

  @override
  String get marketVariety => 'Variety';

  @override
  String marketVarietyValue(String variety) {
    return 'Variety: $variety';
  }

  @override
  String get schemeStatus => 'Status (on source)';

  @override
  String get schemeActiveOnSource => 'Active on source';

  @override
  String get schemeStatusNotStated => 'Status not stated on source';

  @override
  String get schemeComponents => 'Components';

  @override
  String get eligibilitySignIn =>
      'Please sign in again to check your eligibility';

  @override
  String get soilSurvey => 'Survey';

  @override
  String get soilCycle => 'Cycle';

  @override
  String soilParamSamples(String param, int samples) {
    return '$param ($samples samples)';
  }

  @override
  String get soilLow => 'Low';

  @override
  String get soilMedium => 'Medium';

  @override
  String get soilHigh => 'High';

  @override
  String homeGreeting(String name) {
    return 'Hello, $name';
  }

  @override
  String get homeGreetingNoName => 'Hello';

  @override
  String get homeNoFarm => 'No farm added yet';

  @override
  String get homeSetCrop => 'Set the farm\'s crop to match market prices';

  @override
  String get homeMarketSnapshot => 'Market prices (latest observed)';

  @override
  String get homeMarketNeedsFarm =>
      'Set a farm or district to see market prices';

  @override
  String get homeRecentActivity => 'Recent activity';

  @override
  String get homeShortcuts => 'Shortcuts';

  @override
  String get homeSeeAll => 'See all';

  @override
  String soilSamplesCount(int count) {
    return '$count samples';
  }

  @override
  String get homeNoMarketForCrop => 'No market data for this crop';

  @override
  String get voiceOfflineUnavailable =>
      'Offline voice recognition isn\'t available on this phone, so nothing was recorded or uploaded. Please type your question.';

  @override
  String get voiceOfflineLanguageMissing =>
      'The offline speech pack for this language isn\'t installed. Install it in your phone\'s speech settings (for example Google app > Settings > Voice > Offline speech recognition), then try again. You can type your question meanwhile.';

  @override
  String get voiceTtsMissingTamil =>
      'No offline Tamil voice is installed, so the answer can\'t be read aloud. Install it: Settings > General management > Text-to-speech output > engine settings > Install voice data > Tamil.';

  @override
  String get voiceTtsMissingEnglish =>
      'No offline English voice is installed, so the answer can\'t be read aloud. Install it: Settings > General management > Text-to-speech output > engine settings > Install voice data.';

  @override
  String get voiceTtsFailed =>
      'The answer could not be read aloud. Tap the speaker icon to try again.';

  @override
  String get voiceSttError =>
      'Voice input stopped unexpectedly. Please try again or type your question.';

  @override
  String get voiceDismiss => 'Dismiss';

  @override
  String get brandTagline =>
      'Farming guidance for Tamil Nadu, in Tamil and English';

  @override
  String get loginPhoneHelp =>
      'We send a one-time code to this number. No password is needed.';

  @override
  String get homeFarmLabel => 'Your farm';

  @override
  String get homeAskTitle => 'Ask the farming assistant';

  @override
  String get homeAskSubtitle =>
      'Crops, soil, weather and schemes. Sources are shown when they are found.';

  @override
  String get homeAskAction => 'Ask a question';

  @override
  String get homeServices => 'Services';

  @override
  String get moreInfoSection => 'Farm information';

  @override
  String get moreRecordsSection => 'Your records';

  @override
  String get moreAccountSection => 'Account';

  @override
  String get moreWeatherSub => 'Current conditions and 7-day forecast';

  @override
  String get moreMarketSub => 'Observed prices, a snapshot and not live';

  @override
  String get moreSchemesSub => 'Central and state schemes';

  @override
  String get moreSoilSub => 'Regional soil data and your soil tests';

  @override
  String get moreScanSub => 'Under validation, no diagnosis yet';

  @override
  String get moreFarmsSub => 'Add or edit your farms';

  @override
  String get moreDiarySub => 'Notes and farm activity';

  @override
  String get moreSatelliteSub => 'Status of satellite features';

  @override
  String get moreProfileSub => 'Name, district and language';

  @override
  String get moreSettingsSub => 'Language, theme and about';

  @override
  String get assistantEmptyTitle => 'How can I help with your farm?';

  @override
  String get assistantCopy => 'Copy answer';

  @override
  String get assistantCopied => 'Answer copied';

  @override
  String get assistantGeneralGuidance => 'General guidance';

  @override
  String get assistantGeneralGuidanceNote => 'Not from TNAU sources';

  @override
  String get assistantSourcesNote =>
      'Documents retrieved for this answer. They may not support every sentence.';

  @override
  String get assistantNoAnswerTitle => 'No verified answer';

  @override
  String get voiceTapToStop => 'Tap to stop';

  @override
  String get voiceSpeakAnswer => 'Listen';

  @override
  String get scanValidationBadge => 'Under validation';

  @override
  String get scanValidationTitle => 'Disease detection is not available yet';

  @override
  String get scanValidationBody =>
      'The disease model has not been approved for farmer use. A photo you send is not diagnosed. For a crop problem, contact your local agricultural officer.';

  @override
  String get scanHowTitle => 'What you can do here';

  @override
  String get scanHowBody =>
      'Choose a crop and a clear photo of the affected leaf. The app reports honestly whether a validated result is available.';

  @override
  String get marketSnapshotBadge => 'Snapshot, not live';

  @override
  String get settingsAppearance => 'Appearance';

  @override
  String get settingsPrivacy => 'Privacy';

  @override
  String get settingsPrivacyBody =>
      'Your questions are answered by a model running on the UZHAVAN server, not by a paid cloud AI service. Speech is produced by this phone\'s own voice. Weather comes from Open-Meteo using your district\'s location only.';

  @override
  String get settingsVoice => 'Voice';

  @override
  String get settingsVoiceBody =>
      'Answers are read aloud with this phone\'s voice. Speech input needs Android 12 or newer with an offline language pack; otherwise type your question.';
}
