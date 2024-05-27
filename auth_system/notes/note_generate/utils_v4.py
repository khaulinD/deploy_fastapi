

async def handle_note_data(data: dict) -> str:
    text: str = ""

    if data['selectedNoteType'] == "Nursing Note":
        text += ("You are a nurse with 20 years of experience working in US medical facilities in the treatment of addictions and you"
                 " need to write a Nursing Note document to send to insurance company. ")

    elif data['selectedNoteType'] == "Group Note":
        text += ("You are a doctor with 20 year s of experience working in US medical facilities in the treatment of addictions and you"
                 " need to write a Group Note about your patient who is treated in a group and his progress in treatment. ")
    elif data['selectedNoteType'] == "Group Note":
        pass
    elif data['selectedNoteType'] == "Group Note":
        pass
    else:
        text += ("You are a doctor with 20 year s of experience working in US medical facilities in the treatment of addictions and you"
                 " need to write a note about your patient and his progress in treatment. ")

    if data["selectedInsurance"] == "Others":
        text += (f"So write note for insurance company rely on this"
                 f" data(object of some questions and keywords about patient): {data}. ")
    else:
        text += (f"So write note for {data['selectedInsurance']} insurance company based"
                 f" on correct examples of this company`s notes and also rely on"
                 f" this data(object of some questions and keywords about patient): {data}. ")

    if data["selectedNoteFormat"] == "Narrative":
        text += (f"This is must be Narrative note format.")
    elif data["selectedNoteFormat"] == "Dap Note":
        text += (f"This is must be DAP note format so I want that note have 3 topics: Data, Assessment, Plan."
                 f" Use clean and concise language, write it in formal tone.")
    elif data["selectedNoteFormat"] == "SOAP Note":
        text += (f"This is must be SOAP note format so I want that note have 4 topics: Subjective, Objective, Assessment, Plan."
                 f" Use clean and concise language, write it in formal tone.")
    elif data["selectedNoteFormat"] == "Treatment Planning Note":
        text += (f"This is must be Treatment Planning note format. Use clean and concise language, write it in formal tone.")

    return text
