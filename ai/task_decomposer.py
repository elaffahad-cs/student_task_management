from typing import List, Optional
from pydantic import BaseModel, Field

class SubTask(BaseModel):
    title: str = Field(description="عنوان المهمة الفرعية الواضحة والقابلة للتنفيذ")
    estimated_hours: float = Field(description="الوقت المتوقع لإنجاز هذه المهمة بالساعات", default=1.0)

class TaskDecompositionResult(BaseModel):
    is_complex: bool = Field(description="هل المهمة معقدة وتحتاج إلى تقسيم؟")
    reasoning: str = Field(description="سبب القرار باختصار")
    subtasks: List[SubTask] = Field(description="قائمة المهام الفرعية")

def decompose_academic_task(task_title: str, task_description: Optional[str] = "") -> TaskDecompositionResult:
    """
    الخوارزمية الشاملة لتحليل وتقسيم المهام الأكاديمية (محلياً وبدون مفاتيح).
    تقوم بالتحقق من صحة المدخلات، اكتشاف اللغة، وتوليد مهام فرعية منظمة.
    """
    # 1. التحقق من صحة المدخلات (Validation)
    if not task_title or not task_title.strip():
        return TaskDecompositionResult(
            is_complex=False,
            reasoning="خطأ: عنوان المهمة فارغ أو غير صالح للتحليل.",
            subtasks=[]
        )

    # دمج العنوان ووصف المهمة لتحليل شامل
    full_text = f"{task_title} {task_description or ''}".lower()
    
    # 2. قائمة الكلمات المفتاحية الدالة على التعقيد (بالعربية والإنجليزية)
    complex_keywords = [
        # English
        "project", "research", "system", "development", "application", 
        "thesis", "assignment", "presentation", "report", "analysis", "implementation",
        # Arabic
        "مشروع", "بحث", "نظام", "تطوير", "تطبيق", 
        "رسالة", "واجب", "عرض", "تقرير", "تحليل", "تنفيذ"
    ]
    
    # التحقق مما إذا كانت المهمة تحتوي على كلمات تعقيد
    is_complex = any(keyword in full_text for keyword in complex_keywords)

    if is_complex:
        # تحديد اللغة السائدة (هل هي إنجليزية أم عربية؟)
        is_english = any(word in full_text for word in ["project", "research", "system", "development", "report", "presentation", "implementation"])
        
        if is_english:
            subtasks = [
                SubTask(title=f"Research & Data Collection: {task_title}", estimated_hours=2.5),
                SubTask(title=f"Architecture & Initial Planning", estimated_hours=1.5),
                SubTask(title=f"Core Implementation & Drafting", estimated_hours=3.5),
                SubTask(title=f"Testing, Review & Submission", estimated_hours=1.5)
            ]
            reasoning = "تم رصد مهمة أكاديمية معقدة باللغة الإنجليزية، وتم تقسيمها إلى مراحل إجرائية."
        else:
            # تم تصحيح المشكلة هنا بحذف := وتمرير النصوص مباشرة بشكل نظيف وسليم
            subtasks = [
                SubTask(title=f"بحث وجمع المعلومات لـ: {task_title}", estimated_hours=2.5),
                SubTask(title=f"التصميم والتخطيط الأولي", estimated_hours=1.5),
                SubTask(title=f"التنفيذ والكتابة الأساسية", estimated_hours=3.5),
                SubTask(title=f"المراجعة، الاختبار والتسليم النهائي", estimated_hours=1.5)
            ]
            reasoning = "تم رصد مهمة أكاديمية معقدة باللغة العربية، وتم تقسيمها لمساعدة الطالب على منع التسويف."

        return TaskDecompositionResult(
            is_complex=True,
            reasoning=reasoning,
            subtasks=subtasks
        )
    else:
        return TaskDecompositionResult(
            is_complex=False,
            reasoning="المهمة بسيطة، محددة، ولا تتطلب تقسيماً فرعياً.",
            subtasks=[]
        )