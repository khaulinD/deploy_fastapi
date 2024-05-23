data_example = {
    "selectedInsurance": "Magelan",
    "selectedLevelOfCare": "Detox",
    "selectedNoteType": "Physician Note",
    "selectedNoteFormat": "Narrative",
    "patient_name": "John Doe",
    "group_size": 15,  # used in group_note
    "submission_deadline": "2024-05-20",  # used in ur_note
    "time": "10:00 AM",  # used in nursing_note
    "keywordSymptomsBehaviors": ["isolating", "self-centeredness", "crying", "concentration", "problems", "vomiting"]
}

def generate_note(data: dict):
    text = f"Write note for {data['patient_name']} "
    if data['selectedInsurance'] in "Magelan":
        text += f"using {data['selectedInsurance']} insurance company templates "
        operate_lvl_care(text, data)
    elif data['selectedInsurance'] in "Cigna and Evernorth":
        operate_lvl_care(text, data)
    elif data['selectedInsurance'] in "Optum and United Healthcare":
        operate_lvl_care(text, data)
    elif data['selectedInsurance'] in "Aetna":
        operate_lvl_care(text, data)
    elif data['selectedInsurance'] in "Other company":
        text += f"using some insurance company templates "
        operate_lvl_care(text, data)
    else:
        operate_lvl_care(text, data)

def operate_lvl_care(text, data):
    if data['selectedLevelOfCare'] in "Detox":
        text += (f"with {data['selectedLevelOfCare']} level of care."
                 f" \nAlso mensionet that Patient has no signs or symptoms of intoxication or withdrawal. "
                 f"She is able to tolerate withdrawal discomfort.")
        text += f"For patient also has the following this characteristics:"
        for i in data['keywordSymptomsBehaviors']:
            text += f" {i},"

        operate_type(text, data)
    elif data['selectedLevelOfCare'] in "Cigna and Evernorth":
        operate_type(text, data)
    elif data['selectedLevelOfCare'] in "Optum and United Healthcare":
        operate_type(text, data)
    elif data['selectedLevelOfCare'] in "Aetna":
        operate_type(text, data)
    else:
        ...


def operate_type(text, data):

    if data["selectedNoteType"] in "Physician Note":
        text += f"Note must have {data['selectedNoteType']} type. "
        operate_format(text, data)
    elif data["selectedNoteType"] in "Group Note":
        operate_format(text, data)
    elif data["selectedNoteType"] in "Ancillary Progress Not":
        operate_format(text, data)
    elif data["selectedNoteType"] in "UR Note":
        operate_format(text, data)
    elif data["selectedNoteType"] in "Nursing Note":
        operate_format(text, data)
    elif data["selectedNoteType"] in "Individual Note":
        operate_format(text, data)
    elif data["selectedNoteType"] in "Others":
        operate_format(text, data)
    else:
        ...


def operate_format(text, data):

    if data["selectedNoteFormat"] in "Narrative":
        text += f"Note must have {data['selectedNoteFormat']} format. "
        print(text)
    elif data["selectedNoteFormat"] in "Dap Note":
        ...
    elif data["selectedNoteFormat"] in "SOAP Note":
        ...
    elif data["selectedNoteFormat"] in "Treatment Planning Note":
        ...
    else:
        ...




generate_note(data_example)