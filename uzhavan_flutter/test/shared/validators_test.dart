import 'package:flutter_test/flutter_test.dart';
import 'package:uzhavan/shared/utils/validators.dart';

void main() {
  test('Indian mobile: 10 digits starting 6–9', () {
    for (final ok in ['9876543210', '6000000000', '7123456789', '8999999999']) {
      expect(Validators.isValidPhone(ok), isTrue, reason: ok);
    }
    for (final bad in ['5876543210', '987654321', '98765432100', '+919876543210', '98765 43210', '']) {
      expect(Validators.isValidPhone(bad), isFalse, reason: bad);
    }
  });

  test('OTP: exactly 6 digits', () {
    expect(Validators.isValidOtp('123456'), isTrue);
    expect(Validators.isValidOtp('12345'), isFalse);
    expect(Validators.isValidOtp('1234567'), isFalse);
    expect(Validators.isValidOtp('12a456'), isFalse);
  });

  test('Tamil Nadu bounding box', () {
    expect(Validators.isLatInTamilNadu(10.787), isTrue);
    expect(Validators.isLatInTamilNadu(7.9), isFalse);
    expect(Validators.isLatInTamilNadu(13.7), isFalse);
    expect(Validators.isLonInTamilNadu(79.138), isTrue);
    expect(Validators.isLonInTamilNadu(76.1), isFalse);
    expect(Validators.isLonInTamilNadu(80.5), isFalse);
  });

  test('name length 2–100 and decimals', () {
    expect(Validators.isValidName(' a '), isFalse);
    expect(Validators.isValidName('அம'), isTrue);
    expect(Validators.isValidName('x' * 101), isFalse);
    expect(Validators.parseDecimal('10,5'), 10.5);
    expect(Validators.parseDecimal(''), isNull);
    expect(Validators.parseDecimal('abc'), isNull);
  });
}
