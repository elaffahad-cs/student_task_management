import sys
import os

# لضمان عمل الاستيراد بشكل صحيح من أي مجلد
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai.task_decomposer import decompose_academic_task

def test_interactive_student_playground():
    """
    ساحة تجربة تفاعلية لكِ ولزميلاتك لإدخال أي مهمة واختبار استجابة الخوارزمية.
    """
    print("\n" + "=" * 65)
    print("  🧪 ساحة تجربة خوارزمية AI Task Decomposer (للطالبات)  ")
    print("=" * 65)
    
    # قائمة مهام تجريبية يمكنك أنتِ وزميلاتك تعديلها بحرية لتجربة أي شيء!
    custom_tasks_to_try = [
        {"title": "مقال عن الأمن السيبراني", "desc": "كتابة 3 صفحات مع المراجع."},
        {"title": "Mobile App Development Project", "desc": "Build a flutter application."},
        {"title": "مذاكرة اختبار الرياضيات", "desc": "مراجعة الباب الأول."}
    ]
    
    for i, item in enumerate(custom_tasks_to_try, 1):
        print(f"\n[تجربة #{i}] المهمة المدخلة: '{item['title']}'")
        print(f"الوصف: {item['desc']}")
        print("-" * 50)
        
        # استدعاء الخوارزمية الشاملة
        result = decompose_academic_task(item['title'], item['desc'])
        
        print(f"📌 النتيجة: {'معقدة (تم تقسميها ⚠️)' if result.is_complex else 'بسيطة (مهمة مفردة ✅)'}")
        print(f"💬 التقرير: {result.reasoning}")
        
        if result.is_complex:
            print("📋 الخطوات الفرعية المقترحة:")
            for idx, sub in enumerate(result.subtasks, 1):
                print(f"   {idx}. [ ] {sub.title}  ⏱️ ({sub.estimated_hours} ساعات)")
        
        print("=" * 65)

if __name__ == "__main__":
    test_interactive_student_playground()