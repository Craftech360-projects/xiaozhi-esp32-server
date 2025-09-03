import os
import argparse
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from educational_ingestion import EducationalIngestionPipeline
from educational_retriever import EducationalRAGRetriever
from educational_config import Grade, Subject, get_collection_name

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


class EducationalRAGSystem:
    def __init__(self):
        self.ingestion_pipeline = EducationalIngestionPipeline()
    
    def ingest_textbooks(self, 
                        textbook_directory: str,
                        grade: str,
                        subject: str,
                        recreate: bool = False):
        """Ingest textbooks for a specific grade and subject"""
        
        try:
            grade_enum = Grade(grade)
            subject_enum = Subject(subject)
        except ValueError as e:
            print(f"Error: Invalid grade or subject. {e}")
            return
        
        if not Path(textbook_directory).exists():
            print(f"Error: Directory does not exist: {textbook_directory}")
            return
        
        print(f"Starting ingestion for {grade} {subject}...")
        print(f"Directory: {textbook_directory}")
        
        result = self.ingestion_pipeline.ingest_subject_textbooks(
            textbook_directory=textbook_directory,
            grade=grade_enum,
            subject=subject_enum,
            recreate_collection=recreate
        )
        
        if result.get('success', True):
            print("\n✅ Ingestion completed successfully!")
            print(f"📚 Collection: {result['collection_name']}")
            print(f"📄 Total documents: {result['total_documents']}")
            print(f"📑 Chapters covered: {', '.join(map(str, result['chapters_covered']))}")
            print(f"📊 Content breakdown: {result['content_categories']}")
            print(f"🔢 Total vectors: {result['total_points_in_collection']}")
        else:
            print(f"❌ Ingestion failed: {result.get('error', 'Unknown error')}")
    
    def start_learning_session(self, grade: str, subject: str):
        """Start an interactive learning session"""
        
        try:
            grade_enum = Grade(grade)
            subject_enum = Subject(subject)
        except ValueError as e:
            print(f"Error: Invalid grade or subject. {e}")
            return
        
        retriever = EducationalRAGRetriever(grade_enum, subject_enum)
        
        # Check if collection exists
        stats = retriever.get_collection_stats()
        if 'error' in stats:
            print(f"❌ Error: {stats['error']}")
            print(f"💡 Try ingesting textbooks first with: python educational_main.py ingest --grade {grade} --subject {subject} --directory path/to/textbooks")
            return
        
        print(f"\n🎓 Welcome to {grade.title()} {subject.title()} Learning Assistant!")
        print(f"📚 Collection: {stats['collection_name']}")
        print(f"📊 Available content: {stats['total_content']} pieces")
        print("\n" + "="*50)
        
        print("\n💡 What can I help you with?")
        print("  • Ask questions about concepts (e.g., 'What are fractions?')")
        print("  • Get help with problems (e.g., 'How to add fractions?')")
        print("  • Clear doubts (e.g., 'I'm confused about equivalent fractions')")
        print("  • Get chapter summaries (e.g., 'chapter 7 summary')")
        print("  • Type 'quit' to exit")
        print()
        
        while True:
            try:
                user_input = input("🤔 Your question: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Happy learning! See you next time!")
                    break
                
                if not user_input:
                    continue
                
                # Determine query type and respond accordingly
                response = self._process_student_query(retriever, user_input)
                self._display_response(response)
                
            except KeyboardInterrupt:
                print("\n👋 Happy learning! See you next time!")
                break
            except Exception as e:
                print(f"❌ An error occurred: {e}")
    
    def _process_student_query(self, retriever, query: str):
        """Process student query and determine appropriate response type"""
        
        query_lower = query.lower()
        
        # Check for chapter summary requests
        if 'chapter' in query_lower and ('summary' in query_lower or 'summarize' in query_lower):
            # Extract chapter number
            import re
            chapter_match = re.search(r'chapter\s+(\d+)', query_lower)
            if chapter_match:
                chapter_num = int(chapter_match.group(1))
                return retriever.get_chapter_summary(chapter_num)
        
        # Check for doubt clarification keywords
        doubt_keywords = ['confused', 'doubt', 'unclear', "don't understand", 'why', 'how come']
        if any(keyword in query_lower for keyword in doubt_keywords):
            return retriever.clarify_doubt(query)
        
        # Check for problem-solving keywords
        problem_keywords = ['solve', 'calculate', 'find', 'how to', 'step by step', 'method']
        if any(keyword in query_lower for keyword in problem_keywords):
            return retriever.solve_problem(query)
        
        # Default to concept explanation
        return retriever.explain_concept(query)
    
    def _display_response(self, response):
        """Display the response in a student-friendly format"""
        
        if 'error' in response:
            print(f"❌ {response['error']}")
            return
        
        if 'answer' in response:
            print(f"\n** Answer:**")
            print(response['answer'])
            
            # Show sources if available
            if response.get('relevant_content'):
                print(f"\n** Sources:**")
                for i, source in enumerate(response['relevant_content'][:2], 1):
                    chapter_info = ""
                    if source.get('chapter_number') and source.get('chapter_title'):
                        chapter_info = f" (Chapter {source['chapter_number']}: {source['chapter_title']})"
                    print(f"  {i}. {source.get('content_category', 'Content').title()}{chapter_info}")
        
        elif 'summary' in response:
            print(f"\n📖 **Chapter {response['chapter_number']}: {response['chapter_title']}**")
            print(response['summary'])
            
            if response.get('topics_covered'):
                print(f"\n🎯 **Topics Covered:** {', '.join(response['topics_covered'])}")
        
        print("\n" + "-"*50)
    
    def get_overview(self, grade: str, subject: str):
        """Get overview of available content"""
        
        try:
            grade_enum = Grade(grade)
            subject_enum = Subject(subject)
        except ValueError as e:
            print(f"Error: Invalid grade or subject. {e}")
            return
        
        overview = self.ingestion_pipeline.get_collection_overview(grade_enum, subject_enum)
        
        if 'error' in overview:
            print(f"❌ {overview['error']}")
            return
        
        print(f"\n📊 **{grade.title()} {subject.title()} Content Overview**")
        print(f"Collection: {overview['collection_name']}")
        print(f"Total Content: {overview['total_points']} pieces")
        
        if overview.get('chapters'):
            print(f"Chapters Available: {', '.join(map(str, overview['chapters']))}")
        
        if overview.get('content_categories'):
            print("Content Types:")
            for category, count in overview['content_categories'].items():
                print(f"  • {category.title()}: {count}")
        
        if overview.get('files'):
            print(f"Files Processed: {len(overview['files'])}")
            for file in overview['files']:
                print(f"  • {file}")


def main():
    parser = argparse.ArgumentParser(description="Educational RAG System for Textbook Learning")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest textbooks into the system")
    ingest_parser.add_argument("--directory", required=True, help="Directory containing PDF textbooks")
    ingest_parser.add_argument("--grade", required=True, choices=["class-6", "class-7", "class-8", "class-9", "class-10"],
                              help="Grade level")
    ingest_parser.add_argument("--subject", required=True, choices=["mathematics", "science", "english", "social-studies", "hindi"],
                              help="Subject")
    ingest_parser.add_argument("--recreate", action="store_true", help="Recreate collection if it exists")
    
    # Learn command
    learn_parser = subparsers.add_parser("learn", help="Start interactive learning session")
    learn_parser.add_argument("--grade", required=True, choices=["class-6", "class-7", "class-8", "class-9", "class-10"],
                             help="Grade level")
    learn_parser.add_argument("--subject", required=True, choices=["mathematics", "science", "english", "social-studies", "hindi"],
                             help="Subject")
    
    # Overview command
    overview_parser = subparsers.add_parser("overview", help="Get overview of available content")
    overview_parser.add_argument("--grade", required=True, choices=["class-6", "class-7", "class-8", "class-9", "class-10"],
                                help="Grade level")
    overview_parser.add_argument("--subject", required=True, choices=["mathematics", "science", "english", "social-studies", "hindi"],
                                help="Subject")
    
    # Quick query command
    query_parser = subparsers.add_parser("query", help="Ask a quick question")
    query_parser.add_argument("--grade", required=True, choices=["class-6", "class-7", "class-8", "class-9", "class-10"],
                             help="Grade level")
    query_parser.add_argument("--subject", required=True, choices=["mathematics", "science", "english", "social-studies", "hindi"],
                             help="Subject")
    query_parser.add_argument("--question", required=True, help="Your question")
    
    args = parser.parse_args()
    
    system = EducationalRAGSystem()
    
    if args.command == "ingest":
        system.ingest_textbooks(
            textbook_directory=args.directory,
            grade=args.grade,
            subject=args.subject,
            recreate=args.recreate
        )
    
    elif args.command == "learn":
        system.start_learning_session(args.grade, args.subject)
    
    elif args.command == "overview":
        system.get_overview(args.grade, args.subject)
    
    elif args.command == "query":
        try:
            grade_enum = Grade(args.grade)
            subject_enum = Subject(args.subject)
            retriever = EducationalRAGRetriever(grade_enum, subject_enum)
            
            response = system._process_student_query(retriever, args.question)
            system._display_response(response)
            
        except ValueError as e:
            print(f"Error: Invalid grade or subject. {e}")
    
    else:
        # Show help and available collections
        parser.print_help()
        print("\n" + "="*50)
        print("📚 Educational RAG System")
        print("="*50)
        
        subjects = system.ingestion_pipeline.list_available_subjects()
        if subjects:
            print("\n🎓 **Configured Subjects:**")
            for grade, subject_list in subjects.items():
                print(f"  {grade.title()}: {', '.join(subject_list)}")
        
        print("\n💡 **Example Usage:**")
        print("  # Ingest Class 6 Mathematics textbooks")
        print("  python educational_main.py ingest --grade class-6 --subject mathematics --directory ./Class-6-mathematics")
        print("")
        print("  # Start learning session")
        print("  python educational_main.py learn --grade class-6 --subject mathematics")
        print("")
        print("  # Quick question")
        print("  python educational_main.py query --grade class-6 --subject mathematics --question \"What are fractions?\"")


if __name__ == "__main__":
    main()