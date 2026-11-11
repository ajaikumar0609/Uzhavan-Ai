import 'package:flutter_test/flutter_test.dart';
import 'package:uzhavan/shared/utils/area_units.dart';

void main() {
  test('1 acre = 0.404686 ha', () {
    expect(AreaUnits.acresToHectares(1), 0.404686);
    expect(AreaUnits.acresToHectares(2.5), closeTo(1.011715, 1e-9));
  });

  test('hectares → acres', () {
    expect(AreaUnits.hectaresToAcres(0.404686), closeTo(1, 1e-12));
    expect(AreaUnits.hectaresToAcres(1), closeTo(2.4710516, 1e-6));
  });

  test('displays acres to one decimal with no float noise', () {
    expect(AreaUnits.formatAcres(1), '2.5');
    expect(AreaUnits.formatAcres(AreaUnits.acresToHectares(2.5)), '2.5');
    expect(AreaUnits.formatAcres(AreaUnits.acresToHectares(0.04)), '0.0');
    expect(AreaUnits.formatAcres(AreaUnits.acresToHectares(12.46)), '12.5');
  });

  test('round-trips through the edit field', () {
    for (final a in [0.5, 1.0, 2.25, 3.3, 10.0]) {
      final ha = AreaUnits.acresToHectares(a);
      expect(double.parse(AreaUnits.acresForInput(ha)), a);
    }
    expect(AreaUnits.acresForInput(AreaUnits.acresToHectares(4)), '4');
  });
}
