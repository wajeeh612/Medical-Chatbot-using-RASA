from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet
import sqlite3
import requests
import json



class ValidateUserDetailsForm(FormValidationAction):
    """Validates user input for the user_details_form"""

    def name(self) -> Text:
        return "validate_user_details_form"

    def validate_name(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate name input - only letters and spaces allowed"""

        if not slot_value:
            dispatcher.utter_message(response="utter_invalid_name")
            return {"name": None}

        cleaned_name = slot_value.strip()

        if not (cleaned_name and all(char.isalpha() or char.isspace() for char in cleaned_name)):
            dispatcher.utter_message(response="utter_invalid_name")
            return {"name": None}

        if len(''.join(char for char in cleaned_name if char.isalpha())) < 2:
            dispatcher.utter_message(response="utter_invalid_name")
            return {"name": None}

        return {"name": cleaned_name.title()}

    def validate_age(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate age - must be a number between 1 and 120"""

        if not slot_value:
            dispatcher.utter_message(response="utter_invalid_age")
            return {"age": None}

        try:
            age_value = int(slot_value)

            if 1 <= age_value <= 120:
                return {"age": str(age_value)}
            else:
                dispatcher.utter_message(response="utter_invalid_age")
                return {"age": None}
        except ValueError:
            dispatcher.utter_message(response="utter_invalid_age")
            return {"age": None}

    def validate_gender(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate gender - must be male, female, or other"""

        if not slot_value:
            dispatcher.utter_message(response="utter_invalid_gender")
            return {"gender": None}

        valid_genders = {
            "male": "male",
            "m": "male",
            "man": "male",
            "boy": "male",
            "gentleman": "male",
            "female": "female",
            "f": "female",
            "woman": "female",
            "girl": "female",
            "lady": "female",
        }

        gender_lower = slot_value.strip().lower()

        if gender_lower in valid_genders:
            return {"gender": valid_genders[gender_lower]}
        else:
            dispatcher.utter_message(response="utter_invalid_gender")
            return {"gender": None}

    def validate_location(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate location - only letters and spaces allowed"""
        if not slot_value:
            dispatcher.utter_message(response="utter_invalid_location")
            return {"location": None}

        cleaned_location = slot_value.strip()

        if not all(char.isalpha() or char.isspace() for char in cleaned_location):
            dispatcher.utter_message(response="utter_invalid_location")
            return {"location": None}

        return {"location": cleaned_location.title()}


class ValidateSymptomsDetailsForm(FormValidationAction):
    """Validates symptoms input and re-asks if extraction fails"""

    def name(self) -> Text:
        return "validate_symptoms_details_form"

    def validate_medical_symptoms(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate symptom input using LLM extraction"""

        patient_id = tracker.get_slot("patient_id")

        if not patient_id:
            dispatcher.utter_message(text="❌ Error: Patient ID not found. Please restart.")
            return {"medical_symptoms": None}


        try:
            extraction_result = self.extract_symptoms_with_llm(slot_value)
            symptoms_data = extraction_result.get("symptoms", [])



            if not symptoms_data:
                dispatcher.utter_message(
                    text="❌ I couldn't extract any symptoms from your description. Please describe your symptoms more clearly.For example: 'I have a headache for 2 days, severe chest pain for 1 hour."
                )
                return {"medical_symptoms": None}


            conn = sqlite3.connect("medical_data.db")
            cursor = conn.cursor()
            red_flag_triggered = False

            for symptom in symptoms_data:
                is_red_flag = symptom.get("red_flag", False)

                cursor.execute("""
                    INSERT INTO Symptoms (patient_id, symptom, severity, duration, red_flag)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    patient_id,
                    symptom["symptom"],
                    symptom.get("severity", "not specified"),
                    symptom.get("duration", "not specified"),
                    "yes" if is_red_flag else "no"
                ))

                print(f"✅ Stored symptom: {symptom['symptom']} (red_flag: {is_red_flag})")

                if is_red_flag:
                    red_flag_triggered = True

            conn.commit()
            conn.close()


            if red_flag_triggered:
                dispatcher.utter_message(response="utter_emergency")

            return {"medical_symptoms": slot_value}

        except Exception as e:
            print(f"❌ Error in validate_medical_symptoms: {str(e)}")
            import traceback
            traceback.print_exc()
            dispatcher.utter_message(text=f"❌ Error processing symptoms: {str(e)}")
            return {"medical_symptoms": None}

    def extract_symptoms_with_llm(self, user_text: str) -> Dict[str, Any]:
        """Uses Ollama to extract symptoms and detect red flags"""
        prompt = f"""Extract medical symptoms and identify any red flag conditions from the following text.

User input: "{user_text}"

Return ONLY a JSON object in this exact format:
{{
  "symptoms": [
    {{
      "symptom": "symptom name",
      "duration": "duration",
      "severity": "severity level",
      "red_flag": true/false
    }}
  ]
}}

RED FLAG CONDITIONS:
- Chest pain, especially left-sided or radiating to arm/jaw/back
- Severe headache (worst ever, sudden onset)
- Difficulty breathing at rest
- Coughing up blood
- Vomiting blood or blood in stool
- Sudden severe abdominal pain
- Loss of consciousness
- Seizures
- Sudden vision loss or double vision
- Sudden weakness or numbness
- Difficulty speaking
- Severe allergic reaction
- High fever with stiff neck or confusion
- Suicidal thoughts or self-harm ideation
- Severe bleeding that won't stop
- Sudden severe pain (any location)

SYMPTOM EXTRACTION RULES:
- Include symptom, duration, severity, and red_flag (true/false)
- Use "not specified" if duration or severity is missing
- Only extract symptoms that are clearly stated in the text
- If the input is unclear, meaningless, or gibberish, return:
  "symptoms": []
- Return ONLY the JSON object, no other text
"""

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "gemma3:4b",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()
                response_text = response_text.replace('```json', '').replace('```', '').strip()
                extraction_result = json.loads(response_text)

                if isinstance(extraction_result, dict) and "symptoms" in extraction_result:
                    return extraction_result
                else:
                    return {"symptoms": []}
            else:
                return {"symptoms": []}

        except Exception as e:
            print(f"❌ Error calling Ollama: {e}")
            return {"symptoms": []}



class ActionStoreUserDetails(Action):

    def name(self) -> Text:
        return "action_store_user_details"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        name = tracker.get_slot("name")
        age = tracker.get_slot("age")
        gender = tracker.get_slot("gender")
        location = tracker.get_slot("location")
        occupation = tracker.get_slot("occupation")
        medical_history = tracker.get_slot("medical_history")

        try:
            conn = sqlite3.connect("medical_data.db")
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO Patients (name, age, gender, location, occupation, medical_history)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, age, gender, location, occupation, medical_history))

            conn.commit()
            patient_id = cursor.lastrowid
            conn.close()


            return [SlotSet("patient_id", patient_id)]

        except Exception as e:
            dispatcher.utter_message(text=f"❌ Sorry, there was an error saving your information: {str(e)}")
            return []