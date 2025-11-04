import os
import json
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__, template_folder='template', static_folder='static')

try:
    if OPENAI_API_KEY:
        client = OpenAI(api_key=OPENAI_API_KEY)

    else:
        raise ValueError("Missing OPENAI_API_KEY in .env file")
    
except Exception as e:
    print(f"Error during initialization OpenAI client: {e}")
    client = None


#הגדרת הסכמה המצופה
TASK_SCHEMA = {
    "title": "object",
    "porperties": {
        "title": {"type": "string", "description": "כותרת קצרה ותמציתית של המשימה"},
        "dueDate": {"type": "string", "description": "תאריך היעד בפורמט DD-MM-YYYY או null"},
        "dueTime": {"type": "string", "description": "שעת היעד בפורמט HH:MM 24 שעות או null"},
        "category": {"type": "string", "description": "קטגוריה מותאמת למשימה (למשל: 'עבודה', 'אישי', 'סידורים, 'קניות')"},
        "isCompleted": {"type": "boolean", "description": "האם המשימה הושלמה? תמיד False עבור משימה חדשה"},
    },
    "required": ["title", "category"]
}

# System prompt
SYSTEM_PROMPT = (
    "אתה מנתח משימות מומחה. תפקידך הוא לקבל משפט בשפה חופשית, לנתח אותו, "
    "ולחלץ ממנו את כל הפרטים הרלוונטיים (כותרת, תאריך, שעה, קטגוריה) לפורמט JSON מובנה בלבד. "
    "השתמש בעברית לכל ערכי הטקסט. אם לא נמצא פרט ספציפי (כמו תאריך או שעה), השאר את השדה כ-null. "
    "תאריכים צריכים להיות בפורמט YYYY-MM-DD ושעות בפורמט HH:MM."
)

@app.route('/')
def index():
    """מציג את דף הבית של מנהל המשימות"""
    return render_template('index.html')

@app.route('analyze-task', methods=['POST'])
def analyze_task():
    """מקבל טקסט מהfrontend. שולח לOPENAI ומחזיר JSON מובנה"""
    if not client:
        return jsonify({"error": "OpenAI client is not initialized"}), 500
    
    data = request.get_json()
    user_text = data.get('taext', '').strip()

    if not user_text:
        return jsonify({"error": "No text provided"}), 400
    
    try:
        full_prompt = f"נתח את בקשת המשימה הבאה: '{user_text}'"
        
        response = client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "systam", "content": SYSTEM_PROMPT},
                {"role": "user", "content": full_prompt}
            ],
            response_formt={
                "type": "json_schema",
                "json_schema": {
                    "name": "task_schema",
                    "schema": TASK_SCHEMA
                }
            }
        )

        #קבלת תוכן כתוצאה
        json_string = response.output[0].content[0].text.strip()
        parsed_task = json.load(json_string)

        parsed_task['isCompleted'] = False

        return jsonify(parsed_task)

    except Exception as e:
        print(f"שגיאה בניתוח המשימה: {e}")    
        return jsonify({"error": f"failed to analyze task: {e}"}), 500
    

if __name__ == '__main__':
    print("שרת Flask מופעל ומחכה לבקשות...")
    app.run(debug=True)
    