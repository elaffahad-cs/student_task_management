import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:supabase_flutter/supabase_flutter.dart';

class ApiService {
  // ============================================================
  // BASE URL
  // - Android emulator -> 10.0.2.2
  // - iOS simulator / Web / Desktop -> localhost
  // - Real phone -> your PC LAN IP (e.g. 192.168.1.5)
  // ============================================================
  static String get baseUrl {
    // Web
    if (kIsWeb) return 'http://localhost:8000/api/v1';

    // Android emulator
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000/api/v1';
    }

    // iOS simulator / macOS / Windows / Linux
    return 'http://localhost:8000/api/v1';
  }

  // Auth header: send the current Supabase user JWT so backend can identify the user
  static Map<String, String> get _headers {
    final token = Supabase.instance.client.auth.currentSession?.accessToken;
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  // ============================================================
  // TASKS
  // ============================================================

  /// POST /api/v1/tasks?user_id=...
  static Future<Map<String, dynamic>?> createTask({
    required String userId,
    required String title,
    String? description,
    String? subjectName,
    required DateTime deadline,
    int subjectImportance = 3,
    int complexity = 3,
    String? groupId,
  }) async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/tasks?user_id=$userId'), // user_id passed here!
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'title': title,
          'description': description,
          'subject_name': subjectName,
          'deadline': deadline.toUtc().toIso8601String(),
          'subject_importance': subjectImportance,
          'complexity': complexity,
          'group_id': groupId,
        }),
      );
      if (res.statusCode == 200 || res.statusCode == 201) {
        return jsonDecode(res.body) as Map<String, dynamic>;
      }
      debugPrint('createTask failed: ${res.statusCode} ${res.body}');
      return null;
    } catch (e) {
      debugPrint('createTask error: $e');
      return null;
    }
  }

  /// GET /api/v1/tasks?user_id=...
  static Future<List<dynamic>> listTasks(String userId) async {
    try {
      final res = await http.get(
        Uri.parse('$baseUrl/tasks?user_id=$userId'),
      );
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        return data['tasks'] ?? []; // Note: Backend returns {"tasks": [...]}
      }
      return [];
    } catch (e) {
      debugPrint('listTasks error: $e');
      return [];
    }
  }

  // ============================================================
  // GROUPS
  // ============================================================

  /// POST /api/v1/groups  (GroupCreate: name, description)
  static Future<Map<String, dynamic>?> createGroup({
    required String name,
    String? description,
  }) async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/groups'),
        headers: _headers,
        body: jsonEncode({'name': name, 'description': description}),
      );
      if (res.statusCode == 200 || res.statusCode == 201) {
        return jsonDecode(res.body);
      }
      debugPrint('createGroup failed: ${res.statusCode} ${res.body}');
      return null;
    } catch (e) {
      debugPrint('createGroup error: $e');
      return null;
    }
  }

  /// GET /api/v1/groups
  static Future<List<dynamic>> listMyGroups() async {
    try {
      final res = await http.get(
        Uri.parse('$baseUrl/groups'),
        headers: _headers,
      );
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        return data is List ? data : (data['groups'] ?? []);
      }
      return [];
    } catch (e) {
      debugPrint('listMyGroups error: $e');
      return [];
    }
  }

  /// GET /api/v1/groups/{group_id}/members
  static Future<List<dynamic>> listGroupMembers(String groupId) async {
    try {
      final res = await http.get(
        Uri.parse('$baseUrl/groups/$groupId/members'),
        headers: _headers,
      );
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        return data is List ? data : (data['members'] ?? []);
      }
      return [];
    } catch (e) {
      debugPrint('listGroupMembers error: $e');
      return [];
    }
  }

  /// POST /api/v1/groups/{group_id}/members  (MemberAdd: user_id, role?)
  static Future<bool> addGroupMember(String groupId, String userId,
      {String role = 'member'}) async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/groups/$groupId/members'),
        headers: _headers,
        body: jsonEncode({'user_id': userId, 'role': role}),
      );
      return res.statusCode == 200 || res.statusCode == 201;
    } catch (e) {
      debugPrint('addGroupMember error: $e');
      return false;
    }
  }

  /// DELETE /api/v1/groups/{group_id}/members/{user_id}
  static Future<bool> leaveGroup(String groupId, String userId) async {
    try {
      final res = await http.delete(
        Uri.parse('$baseUrl/groups/$groupId/members/$userId'),
        headers: _headers,
      );
      return res.statusCode == 200 || res.statusCode == 204;
    } catch (e) {
      debugPrint('leaveGroup error: $e');
      return false;
    }
  }

  // ============================================================
  // USERS
  // ============================================================

  /// GET /api/v1/users/search?q=...
  static Future<List<dynamic>> searchUsers(String query) async {
    try {
      final res = await http.get(
        Uri.parse('$baseUrl/users/search?q=${Uri.encodeQueryComponent(query)}'),
        headers: _headers,
      );
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        return data is List ? data : (data['users'] ?? []);
      }
      return [];
    } catch (e) {
      debugPrint('searchUsers error: $e');
      return [];
    }
  }

  /// POST /api/v1/users/{user_id}/activity
  static Future<bool> recordActivity(String userId) async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/users/$userId/activity'),
        headers: _headers,
      );
      return res.statusCode == 200;
    } catch (e) {
      debugPrint('recordActivity error: $e');
      return false;
    }
  }

  /// GET /api/v1/users/{user_id}/inactivity
  static Future<Map<String, dynamic>?> getUserInactivity(String userId) async {
    try {
      final res = await http.get(
        Uri.parse('$baseUrl/users/$userId/inactivity'),
        headers: _headers,
      );
      if (res.statusCode == 200) return jsonDecode(res.body);
      return null;
    } catch (e) {
      debugPrint('getUserInactivity error: $e');
      return null;
    }
  }

  // ============================================================
  // COMMITMENT
  // ============================================================

  /// GET /api/v1/commitment/{user_id}
  static Future<Map<String, dynamic>?> getCommitment(String userId) async {
    try {
      final res = await http.get(
        Uri.parse('$baseUrl/commitment/$userId'),
        headers: _headers,
      );
      if (res.statusCode == 200) return jsonDecode(res.body);
      return null;
    } catch (e) {
      debugPrint('getCommitment error: $e');
      return null;
    }
  }

  /// GET /api/v1/groups/{group_id}/commitment
  static Future<Map<String, dynamic>?> getGroupCommitment(
      String groupId) async {
    try {
      final res = await http.get(
        Uri.parse('$baseUrl/groups/$groupId/commitment'),
        headers: _headers,
      );
      if (res.statusCode == 200) return jsonDecode(res.body);
      return null;
    } catch (e) {
      debugPrint('getGroupCommitment error: $e');
      return null;
    }
  }

  // ============================================================
  // NOTIFICATIONS
  // ============================================================

  /// GET /api/v1/notifications
  static Future<List<dynamic>> listNotifications() async {
    try {
      final res = await http.get(
        Uri.parse('$baseUrl/notifications'),
        headers: _headers,
      );
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        return data is List ? data : (data['notifications'] ?? []);
      }
      return [];
    } catch (e) {
      debugPrint('listNotifications error: $e');
      return [];
    }
  }

  /// PATCH /api/v1/notifications/{notification_id}/read
  static Future<bool> markNotificationRead(String notificationId) async {
    try {
      final res = await http.patch(
        Uri.parse('$baseUrl/notifications/$notificationId/read'),
        headers: _headers,
      );
      return res.statusCode == 200;
    } catch (e) {
      debugPrint('markNotificationRead error: $e');
      return false;
    }
  }

  /// PATCH /api/v1/notifications/read-all
  static Future<bool> markAllNotificationsRead() async {
    try {
      final res = await http.patch(
        Uri.parse('$baseUrl/notifications/read-all'),
        headers: _headers,
      );
      return res.statusCode == 200;
    } catch (e) {
      debugPrint('markAllNotificationsRead error: $e');
      return false;
    }
  }

  // ============================================================
  // SCHEDULER (admin / cron only)
  // ============================================================

  /// POST /api/v1/scheduler/check-inactivity
  static Future<bool> runInactivityCheck() async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/scheduler/check-inactivity'),
        headers: _headers,
      );
      return res.statusCode == 200;
    } catch (e) {
      debugPrint('runInactivityCheck error: $e');
      return false;
    }
  }

  /// POST /api/v1/scheduler/deadline-reminders
  static Future<bool> runDeadlineReminders() async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/scheduler/deadline-reminders'),
        headers: _headers,
      );
      return res.statusCode == 200;
    } catch (e) {
      debugPrint('runDeadlineReminders error: $e');
      return false;
    }
  }

  // ============================================================
  // HEALTH
  // ============================================================

  static Future<Map<String, dynamic>?> health() async {
    try {
      final res = await http.get(Uri.parse('http://10.0.2.2:8000/health'));
      if (res.statusCode == 200) return jsonDecode(res.body);
      return null;
    } catch (e) {
      return null;
    }
  }
}
