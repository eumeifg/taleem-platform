"""
Export questions from question bank to a CSV.
"""
import csv
import xmltodict

SUPPORTED_QUESTION_TYPES = {
    # "choiceresponse": "Checkboxes",
    # "optionresponse": "Dropdown",
    "multiplechoiceresponse": "Multiple Choice",
    # "numericalresponse": "Numerical Input",
    # "stringresponse": "Text Input",
}

def export_questions_to_csv(question_bank, csv_file):
    questions = question_bank.get_children()
    max_num_choices = 0
    rows = []
    for question in questions:
        if not question.category == 'problem':
            continue

        question_data = xmltodict.parse(question.data).get("problem", {})
        question_type = next(iter(question_data))
        if question_type not in SUPPORTED_QUESTION_TYPES:
            continue

        question_desc = question_data[question_type]
        choices = [
             "{}:{}".format(choice.get("bdi") or choice.get("#text"), choice["@correct"])
            for choice in question_desc["choicegroup"]["choice"]
        ]
        label = question_desc.get("label", "")
        question_text = label if type(label) is str else label.get("bdi", "")
        rows.append([
            question.display_name,
            question.difficulty_level,
            question.learning_output,
            question.chapter,
            question.topic and question.topic.replace(",", ";") or  "",
            question_text,
            question_desc.get("description", ""),
        ] + choices)
        if len(choices) > max_num_choices:
            max_num_choices = len(choices)

    # write to csv
    writer = csv.writer(csv_file)
    # add header row
    header_row = get_header_row(max_num_choices)
    writer.writerow(header_row)
    # add rest of the rows
    writer.writerows(rows)


def get_header_row(num_choices, question_type="multiplechoiceresponse"):
    return [
        "Display Name",
        "Difficulty Level",
        "Learning Outcome",
        "Chapter",
        "Topics",
        "Question Text",
        "Description",
    ] + [
        "Choice {}".format(num)
        for num in range(1, num_choices + 1)
    ]
