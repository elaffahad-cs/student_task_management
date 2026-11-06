import sys
import os
import pytest

# Force UTF-8 encoding for the terminal to fix Arabic rendering
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai.task_decomposer import decompose_academic_task

# ---------------------------------------------------------
# 1. Automated Tests (For Pytest)
# ---------------------------------------------------------
def test_complex_english_task():
    result = decompose_academic_task("Mobile App Development Project", "Build a flutter application.")
    assert result.is_complex is True
    assert len(result.subtasks) == 4

def test_complex_arabic_task():
    result = decompose_academic_task("مشروع نظام إدارة المهام", "تطوير تطبيق ويب.")
    assert result.is_complex is True
    assert len(result.subtasks) == 4

def test_simple_task():
    result = decompose_academic_task("مذاكرة اختبار الرياضيات", "مراجعة الباب الأول.")
    assert result.is_complex is False

def test_empty_title_validation():
    result = decompose_academic_task("", "Some description")
    assert result.is_complex is False

# ---------------------------------------------------------
# 2. Interactive Playground (Cleaned up for RTL)
# ---------------------------------------------------------
def run_interactive_playground():
    print("\n" + "=" * 70)
    print("  🧪 AI Task Decomposer - Interactive Playground  ")
    print("=" * 70)
    
    custom_tasks_to_try = [
        {"title": "مقال عن الأمن السيبراني", "desc": "كتابة 3 صفحات مع المراجع."},
        {"title": "Mobile App Development Project", "desc": "Build a flutter application."},
        {"title": "مذاكرة اختبار الرياضيات", "desc": "مراجعة الباب الأول."},
        {"title": "مشروع التخرج", "desc": "بناء النظام الذكي."}
    ]
    
    for i, item in enumerate(custom_tasks_to_try, 1):
        print(f"\n--- [Test #{i}] ---")
        # Print Arabic on a new line to help the terminal
        print(f"TASK: {item['title']}")
        print(f"DESC: {item['desc']}")
        
        result = decompose_academic_task(item['title'], item['desc'])
        
        status = "COMPLEX (Decomposed ⚠️)" if result.is_complex else "SIMPLE (Single Task ✅)"
        print(f"STATUS: {status}")
        print(f"REASON: {result.reasoning}")
        
        if result.is_complex:
            print("SUBTASKS:")
            for idx, sub in enumerate(result.subtasks, 1):
                # Putting the title first, then the hours
                print(f"   {idx}. {sub.title} ({sub.estimated_hours} hrs)")
        
        print("-" * 70)

if __name__ == "__main__":
    run_interactive_playground()