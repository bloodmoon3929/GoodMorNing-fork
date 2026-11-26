import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;

class Api {
  static String base = const String.fromEnvironment('API_BASE');
  static Uri uri(String path) =>
      Uri.parse('${base.isEmpty ? Uri.base.origin : base}$path');
  static dynamic check(http.Response response) {
    final data = jsonDecode(utf8.decode(response.bodyBytes));
    if (response.statusCode >= 400) {
      throw Exception(
        data is Map && data['detail'] is String
            ? data['detail']
            : '요청을 처리하지 못했어요. (${response.statusCode})',
      );
    }
    return data;
  }

  static Future<dynamic> get(String path) async =>
      check(await http.get(uri(path)).timeout(const Duration(seconds: 20)));
  static Future<dynamic> save(Map<String, dynamic> diary) async => check(
    await http
        .put(
          uri('/api/diaries/${diary['id']}'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(diary),
        )
        .timeout(const Duration(seconds: 20)),
  );
  static Future<dynamic> upload(
    String path,
    Uint8List bytes,
    String filename,
    Map<String, String> fields,
  ) async {
    final request = http.MultipartRequest('POST', uri(path))
      ..fields.addAll(fields)
      ..files.add(
        http.MultipartFile.fromBytes('photo', bytes, filename: filename),
      );
    return check(
      await http.Response.fromStream(
        await request.send().timeout(const Duration(seconds: 60)),
      ),
    );
  }
}
