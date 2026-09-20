import base64
import json
import logging

from services.onboarding import onboarding_state
from services.story_vocabulary import story_key
from services.curriculum import level_options, normalize_level, topic_options

from asgiref.sync import async_to_sync
from flask import Blueprint, jsonify, render_template, render_template_string, request, session
from markupsafe import escape

from repositories import StoryRepository
from utils.shell import render_page, is_shell_navigation
from utils.story_display import present_story
from utils.story_processing import process_story_words
from utils.story_content import validate_story_title

logger = logging.getLogger(__name__)


def create_comprehension_blueprint(db_path, comprehension_service, drive_service, user_service):
    blueprint = Blueprint("comprehension", __name__)
    story_repository = StoryRepository(db_path)

    def story_for_display(story):
        displayed = present_story(story, session.get("ui_lang", "en"))
        if story.get("text"):
            displayed["capture_key"] = story_key(story["text"])
        return displayed

    def topics_and_stories():
        return topic_options(session.get("ui_lang", "en")), [story_for_display(story) for story in story_repository.list_saved()]

    @blueprint.context_processor
    def curriculum_form_context():
        options = topic_options(session.get('ui_lang', 'en'))
        topic = request.values.get('topic', 'any')
        selected = next((item for item in options if item['value'] == topic), None)
        raw_level = request.form.get('difficulty') if request.method == 'POST' else request.args.get('level')
        level_explicit = bool(raw_level)
        try:
            level = normalize_level(raw_level, legacy='reading') if raw_level else ((selected or {}).get('level') or 'A1')
        except ValueError:
            level_explicit = False
            level = ((selected or {}).get('level') or 'A1')
        return dict(levels=level_options(session.get('ui_lang', 'en')),
                    selected_topic=topic if selected else 'any', selected_level=level,
                    level_explicit=level_explicit)

    def story_words(story_text):
        return process_story_words(
            story_text,
            db_path=db_path,
            drive_service=drive_service,
            added_lemmas=session.get("added_lemmas", set()),
        )

    def submitted_story(story_text, topic, difficulty):
        """Use the persisted title for saved work, including forms opened before retitling."""
        raw_id = request.form.get("story_id")
        story_id = int(raw_id) if raw_id else story_repository.find_existing(story_text, topic, difficulty)
        if story_id:
            saved = story_repository.load(story_id)
            if not saved:
                raise LookupError('Story not found')
            if (saved["text"], saved["topic"], saved["difficulty"]) != (story_text, topic, difficulty):
                raise ValueError("The selected story does not match this activity. Please reload it.")
            return story_id, validate_story_title(saved["title"]), saved.get("title_en", "")
        current = session.get("current_story_data", {})
        cached_title = current.get("title") if current.get("text") == story_text else None
        cached_english = current.get("title_en") if current.get("text") == story_text else None
        title_en = request.form.get("story_title_en") or cached_english
        return None, validate_story_title(request.form.get("story_title") or cached_title), validate_story_title(title_en) if title_en else ""

    def rating_context_matches(story_id, story_text, topic, difficulty, questions):
        # Hidden form fields are editable. Only rate the saved/generated task,
        # while still allowing ordinary feedback on a different question set.
        trusted = story_repository.load(story_id) if story_id else session.get('reading_rating_context', {})
        return bool(trusted and (trusted.get('text'), trusted.get('topic'), trusted.get('difficulty'), trusted.get('questions'))
                    == (story_text, topic, difficulty, questions))

    @blueprint.route("/comprehension", methods=["GET", "POST"])
    def comprehension():
        topics, saved_stories = topics_and_stories()
        logger.debug("Topics: %s, Saved stories: %s", topics, saved_stories)
        if request.method == "GET":
            return render_page(
                "comprehension.html",
                topics=topics,
                saved_stories=saved_stories,
                active_page="comprehension",
            )

        try:
            normalize_level(request.form.get("difficulty", "beginner"), legacy='reading')
            if request.form.get('topic', 'any') not in {'any', *(item['value'] for item in topics)}:
                raise ValueError('Invalid topic')
        except ValueError:
            return render_page('comprehension.html', topics=topics, saved_stories=saved_stories,
                               error=('Выберите тему и уровень из списка.' if session.get('ui_lang') == 'ru' else 'Choose a topic and level from the list.'), active_page='comprehension'), 400

        try:
            topic = str(request.form.get("topic", "any"))
            difficulty = str(request.form.get("difficulty", "beginner"))
            visibility = str(request.form.get("visibility", "revealed"))
            custom_story = request.form.get("custom_story", "").strip()
            logger.debug(
                "POST data: topic=%s, difficulty=%s, visibility=%s, custom_story=%s",
                topic,
                difficulty,
                visibility,
                custom_story[:100],
            )

            if custom_story:
                prepared = async_to_sync(comprehension_service.prepare_story_from_text)(custom_story, topic, difficulty)
            else:
                prepared = async_to_sync(comprehension_service.generate_story)(topic, difficulty)
            title = validate_story_title(prepared.get("title"))
            title_en = validate_story_title(prepared.get("title_en"))
            story_text = prepared["text"]
            questions = prepared["questions"]
            image_url = prepared.get("image_url", "")

            if not image_url:
                image_url = comprehension_service.generate_image(story_text)
            logger.debug("Image URL: %s", image_url)

            audio_url = comprehension_service.generate_audio(story_text)
            logger.debug("Audio URL: %s", audio_url)

            words = story_words(story_text)
            logger.debug("Words data: %s", words[:5])
            story_data = story_for_display({
                "title": title,
                "title_en": title_en,
                "text": story_text,
                "words": words,
                "questions": questions,
                "audio_url": audio_url,
                "image_url": image_url,
                "topic": topic,
                "difficulty": difficulty,
                "answers": [],
            })
            try:
                json.dumps(story_data)
            except ValueError:
                logger.error("JSON serialization error in story_data")
                return render_page(
                    "comprehension.html",
                    topics=topics,
                    saved_stories=saved_stories,
                    error="Invalid story data format",
                    active_page="comprehension",
                ), 500
            session["current_story_text"] = story_text
            session["current_story_data"] = story_data
            # Only provider-created URLs can authorize an unsaved media preview.
            session["generated_story_media"] = [audio_url, image_url]
            session['reading_rating_context'] = {key: story_data[key] for key in ('text', 'topic', 'difficulty', 'questions')}
            session["visibility"] = visibility
            logger.debug("Story data: %s", story_data)
            if request.headers.get("HX-Request") and not is_shell_navigation():
                logger.debug("Rendering _comprehension_content.html for HTMX")
                return render_template("_comprehension_content.html", story=story_data, visibility=visibility)
            logger.debug("Rendering comprehension.html")
            return render_page(
                "comprehension.html",
                topics=topics,
                saved_stories=saved_stories,
                story=story_data,
                visibility=visibility,
                active_page="comprehension",
            )
        except Exception as e:
            logger.error("Comprehension error: %s", str(e), exc_info=True)
            error_message = "Не удалось сгенерировать историю. Попробуйте снова!"
            if request.headers.get("HX-Request") and not is_shell_navigation():
                logger.debug("Returning error div for HTMX")
                return render_template_string('<div class="alert alert-danger">{{ ui_t("comprehension.generation_failed") }}</div>'), 503
            logger.debug("Rendering comprehension.html with error")
            return render_page(
                "comprehension.html",
                topics=topics,
                saved_stories=saved_stories,
                error=error_message,
                active_page="comprehension",
            )

    @blueprint.route("/comprehension/answer", methods=["POST"])
    def answer_questions():
        logger.debug("Raw request data: %s", request.data)
        logger.debug("Form data dict: %s", request.form.to_dict())
        logger.debug("Raw form data: %s", request.form)
        answers = request.form.getlist("answers[]")
        story_text_b64 = request.form.get("story_text", "")
        questions_b64 = request.form.get("questions_b64", "")
        topic = str(request.form.get("topic", "any"))
        difficulty = str(request.form.get("difficulty", "beginner"))
        story_id = request.form.get("story_id", None)

        logger.debug("Raw questions_b64: %s, story_id: %s", questions_b64, story_id)

        try:
            story_text = base64.b64decode(story_text_b64).decode("utf-8")
            logger.debug("Decoded story_text: %s", story_text)
            if questions_b64:
                questions_raw = base64.b64decode(questions_b64).decode("utf-8")
                questions = json.loads(questions_raw)
                logger.debug("Parsed questions: %s", questions)
            else:
                logger.warning("questions_b64 is empty, defaulting to empty list")
                questions = []
        except base64.binascii.Error:
            logger.error("Base64 decode error: story_text_b64=%s, questions_b64=%s", story_text_b64, questions_b64)
            return '<div class="alert alert-danger">Ошибка обработки текста или вопросов</div>', 400
        except json.JSONDecodeError:
            logger.error("JSON decode error, raw questions: %s", questions_raw)
            return '<div class="alert alert-danger">Ошибка обработки вопросов</div>', 400

        if not answers or not questions:
            logger.error("Missing answers or questions: answers=%s, questions=%s", answers, questions)
            return '<div class="alert alert-danger">Ответы или вопросы отсутствуют. Попробуйте снова.</div>', 400

        try:
            user_id = None  # Historical reward compatibility resolves the activity owner.
            story_id, title, title_en = submitted_story(story_text, topic, difficulty)
            feedback, scores, total_score, can_reward = comprehension_service.evaluate_answers(
                story_text, questions, answers, user_id, story_id, topic, difficulty
            )
            logger.debug(
                "Evaluation: feedback=%s, scores=%s, total_score=%s, can_reward=%s",
                feedback,
                scores,
                total_score,
                can_reward,
            )
            feedback_html = ""
            if scores:
                for q, a, f, s in zip(questions, answers, feedback, scores):
                    feedback_html += (
                        f"<p><strong>Вопрос:</strong> {escape(q)}<br><strong>Ваш ответ:</strong> {escape(a)}<br>"
                        f"<strong>Отзыв:</strong> {escape(f)}<br><strong>Оценка:</strong> {escape(s)}/10</p>"
                    )
            else:
                for q, a, f in zip(questions, answers, feedback):
                    feedback_html += (
                        f"<p><strong>Вопрос:</strong> {escape(q)}<br><strong>Ваш ответ:</strong> {escape(a)}<br>"
                        f"<strong>Отзыв:</strong> {escape(f)}</p>"
                    )
            feedback_html += f"<p><strong>Общая оценка:</strong> {total_score:.1f}/10</p>"

            progression_result = {}
            story_id_new = comprehension_service.save_story(
                title=title, title_en=title_en, story_id=story_id, topic=topic, difficulty=difficulty,
                text=story_text, audio_url=request.form.get("audio_url", ""),
                image_url=request.form.get("image_url", ""), questions=questions,
                answers=answers, feedback=feedback, score=total_score,
                assessed=True, progression_result=progression_result,
                fresh_assessment=scores is not None and rating_context_matches(story_id, story_text, topic, difficulty, questions),
            )
            if story_id_new:
                if progression_result.get('coins_earned') and onboarding_state()['coins_introduced']:
                    feedback_html += render_template_string('<p>{{ ui_t("translation.coins") }}: {{ coins }}</p>', coins=progression_result['coins_earned'])
                feedback_html += render_template_string('<p>{{ ui_t("comprehension.saved_ok") }}</p>')
            else:
                logger.error("Failed to save story or find existing story")
                feedback_html += "<p><strong>Error:</strong> Failed to save story</p>"

            return f'<div class="alert alert-info">{feedback_html}</div>'
        except LookupError:
            return '<div class="alert alert-danger">История не найдена</div>', 404
        except Exception:
            logger.error(
                "Answer evaluation error: raw request data=%s, form data=%s",
                request.data,
                request.form.to_dict(),
                exc_info=True,
            )
            feedback_html = "<p><strong>Error:</strong> Failed to evaluate answers</p>"
            return f'<div class="alert alert-danger">{feedback_html}</div>', 500

    @blueprint.route("/comprehension/save", methods=["POST"])
    def save_comprehension():
        logger.debug("Raw form data: %s", request.form.to_dict())
        try:
            story_text_b64 = request.form.get("story_text", "")
            audio_url = request.form.get("audio_url", "")
            image_url = request.form.get("image_url", "")
            questions_b64 = request.form.get("questions_b64", "")
            answers = request.form.getlist("answers[]")
            topic = str(request.form.get("topic", "any"))
            difficulty = str(request.form.get("difficulty", "beginner"))
            user_id = None
            story_id = request.form.get("story_id", None)

            story_text = base64.b64decode(story_text_b64).decode("utf-8")
            questions = json.loads(base64.b64decode(questions_b64).decode("utf-8")) if questions_b64 else []

            story_id, title, title_en = submitted_story(story_text, topic, difficulty)
            feedback, scores, total_score, can_reward = comprehension_service.evaluate_answers(
                story_text, questions, answers, user_id, story_id, topic, difficulty
            )

            story_id_new = comprehension_service.save_story(
                title=title,
                title_en=title_en,
                story_id=story_id,
                topic=topic,
                difficulty=difficulty,
                text=story_text,
                audio_url=audio_url,
                image_url=image_url,
                questions=questions,
                answers=answers,
                feedback=feedback,
                score=total_score,
                assessed=True,
                fresh_assessment=scores is not None and rating_context_matches(story_id, story_text, topic, difficulty, questions),
            )
            if story_id_new:
                logger.debug("Story saved with id %s", story_id_new)
                return render_template_string('<div class="alert alert-success">{{ ui_t("comprehension.saved_ok") }}</div>')
            logger.error("Failed to save story")
            return '<div class="alert alert-danger">Ошибка сохранения истории!</div>', 500
        except LookupError:
            return '<div class="alert alert-danger">История не найдена</div>', 404
        except Exception as e:
            logger.error("Save story error: %s", str(e), exc_info=True)
            return f'<div class="alert alert-danger">Ошибка сохранения: {str(e)}</div>', 500

    @blueprint.route("/comprehension/load/<story_id>")
    def load_comprehension(story_id):
        topics, saved_stories = topics_and_stories()
        logger.debug("Load story: story_id=%s", story_id)

        try:
            story = story_repository.load(story_id)
            if not story:
                logger.error("Story not found: %s", story_id)
                if request.headers.get("HX-Request") and not is_shell_navigation():
                    return '<div class="alert alert-danger">История не найдена</div>', 404
                return render_page(
                    "comprehension.html",
                    topics=topics,
                    saved_stories=saved_stories,
                    error="История не найдена",
                    active_page="comprehension",
                ), 404
            story = story_for_display(story)
            story["words"] = story_words(story["text"])
            session["current_story_text"] = story["text"]
            session["current_story_data"] = story
            session["visibility"] = "revealed"
            logger.debug("Loaded story: %s", story)
            if request.headers.get("HX-Request") and not is_shell_navigation():
                logger.debug("Rendering _comprehension_content.html for HTMX")
                return render_template("_comprehension_content.html", story=story, visibility="revealed")
            logger.debug("Rendering comprehension.html")
            return render_page(
                "comprehension.html",
                topics=topics,
                saved_stories=saved_stories,
                story=story,
                visibility="revealed",
                active_page="comprehension",
            )
        except Exception as e:
            logger.error("Load story error: %s", str(e), exc_info=True)
            error_message = f"Ошибка загрузки: {str(e)}"
            if request.headers.get("HX-Request") and not is_shell_navigation():
                return f'<div class="alert alert-danger">{error_message}</div>'
            return render_page(
                "comprehension.html",
                topics=topics,
                saved_stories=saved_stories,
                error=error_message,
                active_page="comprehension",
            )

    @blueprint.route("/comprehension/generate_more_questions", methods=["POST"])
    def generate_more_questions():
        logger.debug("Raw form data: %s", request.form.to_dict())
        story_text_b64 = request.form.get("story_text", "")
        questions_b64 = request.form.get("questions_b64", "")
        audio_url = request.form.get("audio_url", "")
        image_url = request.form.get("image_url", "")
        topic = str(request.form.get("topic", "any"))
        difficulty = str(request.form.get("difficulty", "beginner"))

        try:
            story_text = base64.b64decode(story_text_b64).decode("utf-8")
            if questions_b64:
                questions_raw = base64.b64decode(questions_b64).decode("utf-8")
                existing_questions = json.loads(questions_raw)
            else:
                logger.warning("questions_b64 is empty, defaulting to empty list")
                existing_questions = []
            logger.debug("Decoded story_text: %s, existing_questions: %s", story_text, existing_questions)

            story_id, title, title_en = submitted_story(story_text, topic, difficulty)
            new_questions = comprehension_service.generate_additional_questions(
                story_text, topic, difficulty, existing_questions
            )
            logger.debug("New questions: %s", new_questions)

            updated_questions = existing_questions + new_questions
            existing_answers = request.form.getlist("answers[]")[:len(existing_questions)]
            existing_answers += [""] * (len(existing_questions) - len(existing_answers))
            previous_story = session.get("current_story_data", {})
            if previous_story.get("text") != story_text:
                previous_story = {}
            story_data = {
                "text": story_text,
                "title": title,
                "title_en": title_en,
                "words": previous_story.get("words", []),
                "questions": updated_questions,
                "answers": existing_answers + [""] * len(new_questions),
                "audio_url": audio_url,
                "image_url": image_url,
                "topic": topic,
                "difficulty": difficulty,
            }
            story_data = story_for_display(story_data)
            if story_id:
                story_data["id"] = story_id
            session["current_story_text"] = story_text
            session["current_story_data"] = story_data
            session["visibility"] = "revealed"
            logger.debug("Updated story_data: %s", story_data)
            return render_template("_questions_partial.html", story=story_data, preserve_answers=True)
        except LookupError:
            return '<div class="alert alert-danger">История не найдена</div>', 404
        except Exception as e:
            logger.error("Generate more questions error: %s", str(e), exc_info=True)
            return render_template_string('<div class="alert alert-danger">{{ ui_t("comprehension.questions_failed") }}</div>'), 503

    return blueprint
