"""
Educational Assistant Agent
Enhanced agent with RAG capabilities for students grades 6-12
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
import pytz
from livekit.agents import (
    Agent,
    RunContext,
    function_tool,
)

from ..services.education_service import EducationService

logger = logging.getLogger("educational_agent")


class EducationalAssistant(Agent):
    """Educational AI Assistant with RAG capabilities for grades 6-12"""

    def __init__(self) -> None:
        super().__init__(
            instructions="""<identity>
You are an educational AI assistant designed to help students from grades 6-12 with their studies.
[Core Characteristics]
- You are knowledgeable about textbook content across multiple subjects
- You provide clear, grade-appropriate explanations
- You can search through textbooks to find accurate information
- You help with homework, concept explanations, and practice problems
- You cite your sources from textbooks when providing information

[Educational Guidelines]
- Always ask for the student's grade level if not specified
- Adjust explanations to be appropriate for the grade level
- Provide step-by-step solutions for problems when requested
- Offer practice problems and examples when helpful
- Encourage learning by asking follow-up questions
- Cite textbook sources (book name and page number) when available

[Subject Areas]
You can help with: Mathematics, Physics, Chemistry, Biology, English, Computer Science, Social Studies, and Economics
</identity>

<interaction_style>
- Be encouraging and supportive
- Break down complex topics into understandable parts
- Use examples and analogies appropriate for the student's age
- Ask clarifying questions when needed
- Offer additional help proactively

Example responses:
"I found this in your Grade 9 Physics textbook, page 45..."
"Let me break this down step by step..."
"Would you like me to find some practice problems for this topic?"
</interaction_style>

<context>
Current student context:
- Grade Level: [STUDENT_GRADE]
- Current Subject: [CURRENT_SUBJECT]
- Local Time: [CURRENT_TIME]
- Date: [TODAY_DATE]
</context>

<tools_available>
You have access to educational tools:
- search_textbook: Search textbooks for information
- explain_concept: Get detailed concept explanations
- get_practice_problems: Find practice problems
- get_step_solution: Get step-by-step solutions
- set_student_context: Set student grade and subject
</tools_available>

IMPORTANT: Always use the educational tools to search textbooks before providing answers. Don't guess or provide information without checking the textbooks first.""",
        )

        # Initialize education service
        self.education_service = EducationService()
        self.is_service_initialized = False

        # Current student context
        self.current_grade = None
        self.current_subject = None

        # Also include existing services for backward compatibility
        self.music_service = None
        self.story_service = None
        self.audio_player = None
        self.unified_audio_player = None

    async def initialize_education_service(self) -> bool:
        """Initialize the education service"""
        try:
            success = await self.education_service.initialize()
            self.is_service_initialized = success
            if success:
                logger.info("Education service initialized successfully")
            else:
                logger.error("Failed to initialize education service")
            return success
        except Exception as e:
            logger.error(f"Error initializing education service: {e}")
            return False

    def set_services(self, music_service, story_service, audio_player, unified_audio_player=None):
        """Set the music and story services (for backward compatibility)"""
        self.music_service = music_service
        self.story_service = story_service
        self.audio_player = audio_player
        self.unified_audio_player = unified_audio_player

    # Educational function tools

    @function_tool
    async def set_student_context(
        self,
        context: RunContext,
        grade: int,
        subject: Optional[str] = None
    ):
        """Set the student's grade level and current subject

        Args:
            grade: Student's grade level (6-12)
            subject: Current subject (optional)
        """
        try:
            if not self.is_service_initialized:
                return "Education service is not available. Please try again later."

            if grade < 6 or grade > 12:
                return "I can only help students in grades 6-12. Please provide a valid grade level."

            success = await self.education_service.set_student_context(grade, subject)
            if success:
                self.current_grade = grade
                self.current_subject = subject

                subject_text = f" for {subject}" if subject else ""
                return f"Great! I've set your grade level to {grade}{subject_text}. I'm ready to help you with your studies!"
            else:
                return "I had trouble setting your grade level. Please try again."

        except Exception as e:
            logger.error(f"Error setting student context: {e}")
            return "I encountered an error. Please try setting your grade level again."

    @function_tool
    async def search_textbook(
        self,
        context: RunContext,
        question: str,
        subject: Optional[str] = None,
        grade: Optional[int] = None
    ):
        """Search textbooks to answer a student's question

        Args:
            question: The student's question
            subject: Subject to search in (optional)
            grade: Grade level (optional, uses current context if not provided)
        """
        try:
            if not self.is_service_initialized:
                return "Education service is not available. Please try again later."

            # Use provided grade or current context
            student_grade = grade or self.current_grade
            target_subject = subject or self.current_subject

            if not student_grade:
                return "I need to know your grade level first. Please tell me what grade you're in (6-12)."

            logger.info(f"Searching textbooks for grade {student_grade}: {question}")

            # Search for answer with simple retry
            logger.info(f"Searching textbooks: {question}")

            try:
                result = await self.education_service.answer_question(
                    question=question,
                    grade=student_grade,
                    subject=target_subject,
                    include_examples=True,
                    include_visual_aids=True
                )

                # Simple retry with a basic format if first attempt fails
                if "error" in result or not result.get("answer") or len(result["answer"].strip()) <= 10:
                    logger.info("First search failed, trying simplified question...")

                    # Try one simple retry
                    simplified_question = f"What is {question.replace('what is', '').replace('What is', '').strip().rstrip('?')}"
                    result = await self.education_service.answer_question(
                        question=simplified_question,
                        grade=student_grade,
                        subject=target_subject,
                        include_examples=True,
                        include_visual_aids=True
                    )

                # If both attempts failed
                if "error" in result or not result.get("answer") or len(result["answer"].strip()) <= 10:
                    return f"I couldn't find information about that topic in your Grade {student_grade} {target_subject or 'science'} textbooks. Try asking about specific concepts or check if this topic is covered in your current chapter."

            except Exception as e:
                logger.error(f"Error during textbook search: {e}")
                return "I encountered an error while searching. Please try again with a different question."

            # Format response
            answer = result["answer"]
            sources = result.get("sources", [])

            # Ensure we have a meaningful answer
            if not answer or len(answer.strip()) < 10:
                return f"I found some information but it's not detailed enough. Could you ask about this topic in a different way? For example, 'What is the definition of [concept]' or 'Explain [concept] in simple terms'."

            # Add source citations
            if sources:
                source_info = sources[0]  # Use first source
                textbook = source_info.get("textbook", "Unknown textbook")
                page = source_info.get("page", "Unknown page")
                answer += f"\n\nSource: {textbook}, page {page}"
            else:
                # Fallback when no sources found
                answer += f"\n\nBased on Grade {student_grade} {target_subject} curriculum."

            # Add examples if available
            if result.get("examples"):
                answer += f"\n\nExample: {result['examples'][0][:200]}..."

            # Add follow-up suggestions
            if result.get("follow_up_suggestions"):
                suggestions = result["follow_up_suggestions"][:2]  # Limit to 2
                answer += f"\n\nYou might also want to ask: {' or '.join(suggestions)}"

            return answer

        except Exception as e:
            logger.error(f"Error searching textbooks: {e}")
            return "I encountered an error while searching. Please try rephrasing your question."

    @function_tool
    async def explain_concept(
        self,
        context: RunContext,
        concept: str,
        subject: Optional[str] = None,
        detail_level: str = "medium"
    ):
        """Get a detailed explanation of a concept

        Args:
            concept: The concept to explain
            subject: Subject area (optional)
            detail_level: Level of detail - basic, medium, or advanced
        """
        try:
            if not self.is_service_initialized:
                return "Education service is not available. Please try again later."

            if not self.current_grade:
                return "I need to know your grade level first. Please tell me what grade you're in (6-12)."

            logger.info(f"Explaining concept '{concept}' for grade {self.current_grade}")

            # First try the dedicated explain_concept method
            result = await self.education_service.explain_concept(
                concept=concept,
                grade=self.current_grade,
                subject=subject or self.current_subject,
                detail_level=detail_level
            )

            # If that fails, try simple fallback
            if "error" in result or not result.get("explanation") or len(result.get("explanation", "").strip()) < 10:
                logger.info("Primary explanation failed, trying basic question...")

                # Try one simple fallback
                basic_query = f"What is {concept}?"
                result = await self.education_service.answer_question(
                    question=basic_query,
                    grade=self.current_grade,
                    subject=subject or self.current_subject
                )

                # If still failed, provide helpful fallback
                if "error" in result or not result.get("answer") or len(result.get("answer", "").strip()) <= 10:
                    return f"I couldn't find a detailed explanation of '{concept}' in your Grade {self.current_grade} {subject or 'science'} textbooks. This concept might be covered in a different chapter or you could try asking about related topics."

            # Format explanation
            explanation = result.get("explanation") or result.get("answer", "")
            sources = result.get("sources", [])

            # Ensure we have content
            if not explanation or len(explanation.strip()) < 5:
                return f"I found '{concept}' mentioned in your textbooks but don't have a complete explanation. Could you ask about this in a more specific way?"

            # Add source citation
            if sources:
                source = sources[0]
                textbook = source.get("textbook", "Unknown textbook")
                page = source.get("page", "Unknown page")
                explanation += f"\n\nSource: {textbook}, page {page}"
            else:
                explanation += f"\n\nBased on Grade {self.current_grade} curriculum."

            return explanation

        except Exception as e:
            logger.error(f"Error explaining concept: {e}")
            return "I encountered an error while explaining that concept. Please try again."

    @function_tool
    async def get_practice_problems(
        self,
        context: RunContext,
        topic: str,
        difficulty: str = "medium",
        count: int = 3
    ):
        """Get practice problems for a specific topic

        Args:
            topic: Topic to get problems for
            difficulty: Difficulty level - easy, medium, or hard
            count: Number of problems to get (1-5)
        """
        try:
            if not self.is_service_initialized:
                return "Education service is not available. Please try again later."

            if not self.current_grade:
                return "I need to know your grade level first. Please tell me what grade you're in (6-12)."

            # Limit count to reasonable range
            count = max(1, min(count, 5))

            logger.info(f"Getting {count} practice problems for '{topic}', difficulty: {difficulty}")

            try:
                result = await self.education_service.get_practice_problems(
                    topic=topic,
                    grade=self.current_grade,
                    subject=self.current_subject,
                    difficulty=difficulty,
                    count=count
                )

                if "error" in result:
                    return f"I couldn't find practice problems for '{topic}' in your Grade {self.current_grade} {self.current_subject or 'science'} materials. Try asking for problems on fundamental concepts in this subject."

                # Format problems
                problems = result.get("problems", [])
                if not problems:
                    return f"I found the topic '{topic}' but no practice problems are available. You could try asking for concept explanations or examples instead."

            except TimeoutError:
                logger.error(f"Timeout while searching for practice problems: {topic}")
                return "The search is taking too long. Please try asking for practice problems on a more specific topic."
            except ConnectionError:
                logger.error(f"Connection error while searching for practice problems: {topic}")
                return "I'm having trouble connecting to the educational database. Please try again in a moment."

            response = f"Here are {len(problems)} practice problems for {topic}:\n\n"

            for i, problem in enumerate(problems, 1):
                response += f"Problem {i}: {problem['problem_text']}\n"
                if problem.get("hints"):
                    response += f"Hint: {', '.join(problem['hints'][:2])}\n"  # Max 2 hints
                response += "\n"

            response += "Would you like me to show you how to solve any of these problems?"

            return response

        except Exception as e:
            logger.error(f"Error getting practice problems: {e}")
            return "I encountered an error while finding practice problems. Please try again."

    @function_tool
    async def get_step_solution(
        self,
        context: RunContext,
        problem: str
    ):
        """Get a step-by-step solution for a problem

        Args:
            problem: The problem to solve step by step
        """
        try:
            if not self.is_service_initialized:
                return "Education service is not available. Please try again later."

            if not self.current_grade:
                return "I need to know your grade level first. Please tell me what grade you're in (6-12)."

            logger.info(f"Getting step-by-step solution for: {problem}")

            result = await self.education_service.get_step_by_step_solution(
                problem=problem,
                grade=self.current_grade,
                subject=self.current_subject
            )

            if "error" in result:
                return f"I couldn't find a solution method for this problem. {result['error']}"

            # Format solution
            steps = result.get("steps", [])
            if not steps:
                return "I found some information about this problem, but couldn't break it down into clear steps."

            response = f"Here's how to solve this step by step:\n\n"

            for i, step in enumerate(steps, 1):
                response += f"Step {i}: {step}\n\n"

            # Add source
            source = result.get("source", {})
            if source.get("textbook"):
                response += f"Source: {source['textbook']}, page {source.get('page', 'Unknown')}"

            return response

        except Exception as e:
            logger.error(f"Error getting step solution: {e}")
            return "I encountered an error while finding the solution. Please try again."

    @function_tool
    async def search_by_topic(
        self,
        context: RunContext,
        topic: str,
        content_type: Optional[str] = None
    ):
        """Search for content by a specific topic

        Args:
            topic: Topic to search for
            content_type: Type of content - definition, example, exercise, etc.
        """
        try:
            if not self.is_service_initialized:
                return "Education service is not available. Please try again later."

            if not self.current_grade or not self.current_subject:
                return "I need to know your grade level and subject first. Please set your context."

            logger.info(f"Searching for topic '{topic}', content type: {content_type}")

            result = await self.education_service.search_by_topic(
                topic=topic,
                grade=self.current_grade,
                subject=self.current_subject,
                content_type=content_type
            )

            if "error" in result:
                return f"I couldn't find information about '{topic}'. {result['error']}"

            results = result.get("results", [])
            if not results:
                return f"I didn't find any content for the topic '{topic}'. Try searching for a related topic."

            # Format results
            response = f"I found {len(results)} items about '{topic}':\n\n"

            for i, item in enumerate(results[:3], 1):  # Limit to 3 results
                response += f"{i}. {item['content'][:200]}...\n"
                response += f"   Source: {item['textbook']}, {item['page_reference']}\n\n"

            if len(results) > 3:
                response += f"...and {len(results) - 3} more results.\n\n"

            response += "Would you like me to explain any of these topics in more detail?"

            return response

        except Exception as e:
            logger.error(f"Error searching by topic: {e}")
            return "I encountered an error while searching. Please try again."

    # Keep existing music/story functions for backward compatibility

    @function_tool
    async def play_music(
        self,
        context: RunContext,
        song_name: Optional[str] = None,
        language: Optional[str] = None
    ):
        """Play music (for younger students or breaks)"""
        try:
            if not self.music_service or not self.audio_player:
                return "Music service is not available right now."

            # Simple music play functionality
            if song_name:
                songs = await self.music_service.search_songs(song_name, language)
                if songs:
                    song = songs[0]
                else:
                    song = await self.music_service.get_random_song(language)
            else:
                song = await self.music_service.get_random_song(language)

            if not song:
                return "Sorry, I couldn't find any music to play right now."

            # Play the song
            await self.audio_player.play_audio_url(song.get('file_path', ''))

            return f"Playing '{song['title']}' for you! This is a nice break from studying."

        except Exception as e:
            logger.error(f"Error playing music: {e}")
            return "I had trouble playing music. Let's get back to studying!"

    @function_tool
    async def get_study_stats(self, context: RunContext):
        """Get statistics about available educational content"""
        try:
            if not self.is_service_initialized:
                return "Education service is not available right now."

            stats = await self.education_service.get_service_stats()

            if "error" in stats:
                return "I couldn't get the statistics right now."

            collections = stats.get("collections", {})
            total_collections = collections.get("total_collections", 0)
            total_content = collections.get("total_points", 0)

            response = f"I have access to {total_collections} textbook collections "
            response += f"with {total_content} pieces of educational content. "

            if self.current_grade:
                response += f"You're currently set for Grade {self.current_grade}"
                if self.current_subject:
                    response += f" in {self.current_subject}"
                response += "."
            else:
                response += "Please tell me your grade level so I can help you better!"

            return response

        except Exception as e:
            logger.error(f"Error getting study stats: {e}")
            return "I couldn't get the statistics right now, but I'm ready to help with your questions!"

    @function_tool
    async def stop_audio(self, context: RunContext):
        """Stop any currently playing audio and return to listening state"""
        try:
            from ..utils.audio_state_manager import audio_state_manager
            import json

            # Send stop signal to device via data channel
            try:
                stop_data = {
                    "type": "audio_playback_stopped"
                }
                # Try different ways to access the room
                room = None
                if hasattr(context, 'room'):
                    room = context.room
                elif self.unified_audio_player and self.unified_audio_player.context:
                    room = self.unified_audio_player.context.room
                elif self.audio_player and self.audio_player.context:
                    room = self.audio_player.context.room

                if room:
                    await room.local_participant.publish_data(
                        json.dumps(stop_data).encode(),
                        topic="audio_control"
                    )
                    logger.info("Sent audio_playback_stopped via data channel")
                else:
                    logger.warning("Could not access room for data channel")
            except Exception as e:
                logger.warning(f"Failed to send stop signal: {e}")

            # Stop both audio players
            stopped_any = False

            if self.unified_audio_player:
                try:
                    await self.unified_audio_player.stop()
                    stopped_any = True
                    logger.info("Stopped unified audio player")
                except Exception as e:
                    logger.warning(f"Error stopping unified audio player: {e}")

            if self.audio_player:
                try:
                    await self.audio_player.stop()
                    stopped_any = True
                    logger.info("Stopped foreground audio player")
                except Exception as e:
                    logger.warning(f"Error stopping foreground audio player: {e}")

            # Force the system back to listening state
            was_playing = audio_state_manager.force_listening_state()

            if was_playing or stopped_any:
                # Send explicit agent state change to ensure device returns to listening
                try:
                    agent_state_data = {
                        "type": "agent_state_changed",
                        "data": {
                            "old_state": "speaking",
                            "new_state": "listening"
                        }
                    }
                    # Try different ways to access the room
                    room = None
                    if hasattr(context, 'room'):
                        room = context.room
                    elif self.unified_audio_player and self.unified_audio_player.context:
                        room = self.unified_audio_player.context.room
                    elif self.audio_player and self.audio_player.context:
                        room = self.audio_player.context.room

                    if room:
                        await room.local_participant.publish_data(
                            json.dumps(agent_state_data).encode(),
                            reliable=True
                        )
                        logger.info("Sent forced agent_state_changed to listening")
                    else:
                        logger.warning("Could not access room for listening state signal")
                except Exception as e:
                    logger.warning(f"Failed to send listening state signal: {e}")

                return "Stopped educational content. Ready to continue learning."
            else:
                return "No audio is currently playing. How can I help with your studies?"

        except Exception as e:
            logger.error(f"Error stopping audio: {e}")
            return "Sorry, I encountered an error while trying to stop audio."

