# def generate_note(data: dict):
#     # Define functions for each note type, possibly using more data
#     def physician_note():
#         # Assume additional data needed is provided in data dict
#         print(f"Processing Physician Note for {data['patient_name']}")
#         # More specific operations here...
#
#     def group_note():
#         print(f"Group Note session with {data['group_size']} participants")
#         # More specific operations here...
#
#     def ancillary_progress_note():
#         print("Processing Ancillary Progress Note")
#         # More specific operations here...
#
#     def ur_note():
#         print("UR Note needs to be submitted by", data['submission_deadline'])
#         # More specific operations here...
#
#     def nursing_note():
#         print(f"Nursing Note for patient {data['patient_name']} at {data['time']}")
#         # More specific operations here...
#
#     def individual_note():
#         print("Individual Note with customized details")
#         # More specific operations here...
#
#     # 4.
#     note_operations = {
#         "Physician Note": physician_note,
#         "Group Note": group_note,
#         "Ancillary Progress Not": ancillary_progress_note,
#         "UR Note": ur_note,
#         "Nursing Note": nursing_note,
#         "Individual Note": individual_note,
#     }
#
#     # 3. Define allowed formate for note
#     note_formate = {
#         "Narrative": note_operations,
#         "Dap Note": note_operations,
#         "SOAP Note": note_operations,
#         "Treatment Planning Note": note_operations,
#     }
#
#     # 2. Define allowed levels of care and their specific note types
#     level_of_care_operations = {
#         "Detox": note_formate,
#         "Residential Treatment": note_formate,
#         "Day Treatment": note_formate,
#         "Intensive Outpatient (IOP)": note_formate,
#         "Ambulatory Detox": note_formate
#     }
#
#     # 1. Define allowed insurances and their respective levels of care
#     insurance_operations = {
#         "Magelan": level_of_care_operations,
#         "Cigna and Evernorth": level_of_care_operations,
#         "Optum and United Healthcare": level_of_care_operations,
#         "Aetna": level_of_care_operations,
#     }
#
#     # Access the relevant operation based on the input data
#     try:
#         note_type_operation = insurance_operations[data["selectedInsurance"]] \
#             [data["selectedLevelOfCare"]] \
#             [data["selectedNoteFormat"]] \
#             [data["selectedNoteType"]]
#
#
#         note_type_operation()  # Execute the operation with custom data handling
#     except KeyError:
#         print("Invalid insurance, level of care, or note type provided")
#
#
# # Example usage
# data_example = {
# "selectedInsurance": "Magelan",
# "selectedLevelOfCare": "Detox",
# "selectedNoteType": "Physician Note",
# "selectedNoteFormat": "Narrative",
# "patient_name": "John Doe",
# "group_size": 15,  # used in group_note
# "submission_deadline": "2024-05-20",  # used in ur_note
# "time": "10:00 AM"  # used in nursing_note
# }
# generate_note(data_example)
from notes.note_generate.create_note import generate_note


async def gen_note(data: str):
    re = f"You are a doctor with 20 year s of experience as USA and you need to write a note about your patient and his progress in treatment.So write note for insurance company rely on this data(object of some questions and keywords about patient): {data}. This is must ne Narrative note. Use clean and concise language, write it in formal tone."
    return await generate_note(messages=re)
# SOAP note so I want that note have 3 topics: Subjective, Objective, Assessment, Plan.