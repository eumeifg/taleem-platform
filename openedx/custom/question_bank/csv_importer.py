"""
Import questions from CSV to a question bank.
"""
import csv
from uuid import uuid4
from xmodule.modulestore.django import modulestore


def import_questions_from_csv(user_id, library_key, csv_filepath):
    questions = []

    # read csv
    with open(csv_filepath, encoding='utf-8') as csv_file:
        reader = csv.reader(csv_file)
        next(reader, None)  # skip the headers
        for row in reader:
            choices = [
                choice_str.split(":")
                for choice_str in row[7:]
            ]
            questions.append({
                "display_name": row[0],
                "difficulty_level": row[1],
                "learning_output": row[2],
                "chapter": row[3],
                "topics": row[4] and row[4].replace(";", ","),
                "question_text": row[5],
                "question_description": row[6],
                "choices": choices,
            })

    # create questions
    create_questions(library_key, user_id, questions)


def create_questions(usage_key, user_id, questions):
    """
    Create and add questions in a given question bank.
    """
    store = modulestore()
    category = 'problem'
    boilerplate = 'multiplechoice.yaml'
    with store.bulk_operations(usage_key.course_key):
        parent = store.get_item(usage_key)
        # get the metadata, display_name, and definition from the caller
        clz = parent.runtime.load_block_type(category)
        template = clz.get_template(boilerplate)
        metadata = template.get('metadata', {})
        data = """
        <problem>
            <multiplechoiceresponse>
                <label><bdi>{question_text}</bdi></label>
                <description>{question_description}</description>
                <choicegroup type="MultipleChoice">
                    {choicegroup}
                </choicegroup>
            </multiplechoiceresponse>
        </problem>
        """
        for question in questions:
            dest_usage_key = usage_key.replace(category=category, name=uuid4().hex)
            metadata.update({
                'display_name': question['display_name'],
                'difficulty_level': question['difficulty_level'],
                'learning_output': question['learning_output'],
                'chapter': question['chapter'],
                'topic': question['topics'],
            })
            choicegroup = create_choicegroup(question['choices'])
            definition_data = {
                'data': data.format(
                    question_text=question['question_text'],
                    question_description=question['question_description'],
                    choicegroup=choicegroup,
                )
            }

            created_block = store.create_child(
                user_id,
                usage_key,
                dest_usage_key.block_type,
                block_id=dest_usage_key.block_id,
                definition_data=definition_data,
                metadata=metadata,
                runtime=parent.runtime,
            )


def create_choicegroup(choices):
    """
    Given the list of list containing
    the choice text and correctness, prepare
    the xml string for choicegroup tag
    """
    choices_xml = ''
    choice_tag = """
        <choice correct="{correct}">
            <bdi>{choice_text}</bdi>
        </choice>
    """
    for choice_info in choices:
        choices_xml += choice_tag.format(
            choice_text=choice_info[0],
            correct=choice_info[1]
        )
    return choices_xml
