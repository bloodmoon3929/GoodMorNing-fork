import 'package:flutter_test/flutter_test.dart';
import 'package:goodmorning/api.dart';
import 'package:http/http.dart' as http;

void main() {
  test('Server error detail is shown to the user', () {
    expect(
      () => Api.check(http.Response('{"detail":"GPU unavailable"}', 409)),
      throwsA(predicate((e) => e.toString().contains('GPU unavailable'))),
    );
  });
  test('API parses successful job response', () {
    expect(
      Api.check(http.Response('{"id":"job-123","state":"queued"}', 202))['id'],
      'job-123',
    );
  });
}
