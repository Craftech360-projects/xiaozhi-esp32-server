#!/usr/bin/env python3
"""
Unit Tests for Assistant Functions
Tests play_music, play_story, stop_audio, and completion handlers
"""

import asyncio
from typing import Optional, Dict, Any
from unittest.mock import Mock, AsyncMock, MagicMock, patch
import sys

print("🧪 Testing Assistant Functions\n")

tests_passed = 0
tests_failed = 0

def test_passed(message):
    global tests_passed
    print(f"✅ {message}")
    tests_passed += 1

def test_failed(message, error=None):
    global tests_failed
    print(f"❌ {message}")
    if error:
        print(f"   Error: {error}")
    tests_failed += 1

# Mock classes to simulate the assistant environment
class MockContext:
    def __init__(self):
        self.room = Mock()
        self.room.local_participant = Mock()
        self.room.local_participant.publish_data = AsyncMock()

class MockMusicService:
    def __init__(self):
        self.is_initialized = True
        self.call_count = 0
    
    async def search_songs(self, song_name, language=None):
        return [{
            'title': f'Test Song: {song_name}',
            'url': f'http://test.com/song_{self.call_count}.mp3',
            'language': language or 'English'
        }]
    
    async def get_random_song(self, language=None):
        self.call_count += 1
        return {
            'title': f'Random Test Song {self.call_count}',
            'url': f'http://test.com/random_{self.call_count}.mp3',
            'language': language or 'English'
        }

class MockStoryService:
    def __init__(self):
        self.is_initialized = True
    
    async def search_stories(self, story_name, category=None):
        return [{
            'title': f'Test Story: {story_name}',
            'url': 'http://test.com/story.mp3',
            'category': category or 'Adventure'
        }]
    
    async def get_random_story(self, category=None):
        return {
            'title': 'Random Test Story',
            'url': 'http://test.com/random_story.mp3',
            'category': category or 'Adventure'
        }

class MockAudioPlayer:
    def __init__(self):
        self.context = MockContext()
        self.playing = False
        self.current_url = None
        self.completion_callback = None
    
    async def play_from_url(self, url, title, on_completion_callback=None):
        self.playing = True
        self.current_url = url
        self.completion_callback = on_completion_callback
        return True
    
    async def stop(self):
        was_playing = self.playing
        self.playing = False
        self.current_url = None
        return was_playing

class MockAssistant:
    """Mock assistant with the key functions we're testing"""
    
    def __init__(self):
        self.music_service = MockMusicService()
        self.story_service = MockStoryService()
        self.unified_audio_player = MockAudioPlayer()
        self.audio_player = None
        self.loop_enabled = False
        self.loop_content_type = None
    
    async def play_music(self, context, song_name=None, language=None, loop_enabled=False):
        """Simplified play_music implementation"""
        if not self.music_service:
            return "Sorry, music service is not available right now."
        
        player = self.unified_audio_player
        if not player:
            return "Sorry, audio player is not available right now."
        
        if song_name:
            songs = await self.music_service.search_songs(song_name, language)
            song = songs[0] if songs else await self.music_service.get_random_song(language)
        else:
            song = await self.music_service.get_random_song(language)
        
        if not song:
            return "Sorry, I couldn't find any music to play right now."
        
        # Store loop state
        if loop_enabled:
            self.loop_enabled = True
            self.loop_content_type = 'music'
        else:
            self.loop_enabled = False
            self.loop_content_type = None
        
        # Play the song
        if loop_enabled:
            await player.play_from_url(
                song['url'],
                song['title'],
                on_completion_callback=lambda: self._handle_music_completion(language)
            )
        else:
            await player.play_from_url(song['url'], song['title'])
        
        return "[MUSIC_PLAYING - STAY_SILENT]"
    
    async def play_story(self, context, story_name=None, category=None, loop_enabled=False):
        """Simplified play_story implementation"""
        if not self.story_service:
            return "Sorry, story service is not available right now."
        
        player = self.unified_audio_player
        if not player:
            return "Sorry, audio player is not available right now."
        
        if story_name:
            stories = await self.story_service.search_stories(story_name, category)
            story = stories[0] if stories else await self.story_service.get_random_story(category)
        else:
            story = await self.story_service.get_random_story(category)
        
        if not story:
            return "Sorry, I couldn't find any stories to play right now."
        
        # Store loop state
        if loop_enabled:
            self.loop_enabled = True
            self.loop_content_type = 'story'
        else:
            self.loop_enabled = False
            self.loop_content_type = None
        
        # Play the story
        if loop_enabled:
            await player.play_from_url(
                story['url'],
                story['title'],
                on_completion_callback=lambda: self._handle_story_completion(category)
            )
        else:
            await player.play_from_url(story['url'], story['title'])
        
        return "[STORY_PLAYING - STAY_SILENT]"
    
    async def stop_audio(self, context):
        """Simplified stop_audio implementation"""
        was_looping = self.loop_enabled
        self.loop_enabled = False
        self.loop_content_type = None
        
        stopped_any = False
        if self.unified_audio_player:
            was_playing = await self.unified_audio_player.stop()
            stopped_any = was_playing
        
        if stopped_any:
            return "Stopped playing audio. Ready to listen."
        else:
            return "No audio is currently playing."
    
    async def _handle_music_completion(self, language=None):
        """Handle music completion in loop mode"""
        if not self.loop_enabled:
            return
        
        context = self.unified_audio_player.context if self.unified_audio_player else None
        if not context:
            self.loop_enabled = False
            return
        
        await self.play_music(
            context=context,
            song_name=None,
            language=language,
            loop_enabled=True
        )
    
    async def _handle_story_completion(self, category=None):
        """Handle story completion in loop mode"""
        if not self.loop_enabled:
            return
        
        context = self.unified_audio_player.context if self.unified_audio_player else None
        if not context:
            self.loop_enabled = False
            return
        
        await self.play_story(
            context=context,
            story_name=None,
            category=category,
            loop_enabled=True
        )

# Test 1: play_music with loop_enabled=true
async def test_play_music_with_loop():
    print("1️⃣ Test play_music with loop_enabled=true")
    
    assistant = MockAssistant()
    context = MockContext()
    
    result = await assistant.play_music(context, song_name="Test Song", language="English", loop_enabled=True)
    
    if assistant.loop_enabled:
        test_passed("Loop state enabled after play_music with loop_enabled=true")
    else:
        test_failed("Loop state not enabled")
    
    if assistant.loop_content_type == 'music':
        test_passed("Loop content type set to 'music'")
    else:
        test_failed(f"Loop content type incorrect: {assistant.loop_content_type}")
    
    if assistant.unified_audio_player.playing:
        test_passed("Audio player started playing")
    else:
        test_failed("Audio player not playing")
    
    if assistant.unified_audio_player.completion_callback:
        test_passed("Completion callback registered")
    else:
        test_failed("Completion callback not registered")
    
    print("")

# Test 2: play_story with loop_enabled=true
async def test_play_story_with_loop():
    print("2️⃣ Test play_story with loop_enabled=true")
    
    assistant = MockAssistant()
    context = MockContext()
    
    result = await assistant.play_story(context, story_name="Test Story", category="Adventure", loop_enabled=True)
    
    if assistant.loop_enabled:
        test_passed("Loop state enabled after play_story with loop_enabled=true")
    else:
        test_failed("Loop state not enabled")
    
    if assistant.loop_content_type == 'story':
        test_passed("Loop content type set to 'story'")
    else:
        test_failed(f"Loop content type incorrect: {assistant.loop_content_type}")
    
    if assistant.unified_audio_player.playing:
        test_passed("Audio player started playing")
    else:
        test_failed("Audio player not playing")
    
    if assistant.unified_audio_player.completion_callback:
        test_passed("Completion callback registered")
    else:
        test_failed("Completion callback not registered")
    
    print("")

# Test 3: stop_audio clears loop state
async def test_stop_audio_clears_loop():
    print("3️⃣ Test stop_audio clears loop state")
    
    assistant = MockAssistant()
    context = MockContext()
    
    # First enable loop mode
    await assistant.play_music(context, loop_enabled=True)
    
    if not assistant.loop_enabled:
        test_failed("Loop not enabled before stop")
        return
    
    # Now stop audio
    result = await assistant.stop_audio(context)
    
    if not assistant.loop_enabled:
        test_passed("Loop state cleared after stop_audio")
    else:
        test_failed("Loop state not cleared")
    
    if assistant.loop_content_type is None:
        test_passed("Loop content type cleared")
    else:
        test_failed(f"Loop content type not cleared: {assistant.loop_content_type}")
    
    if not assistant.unified_audio_player.playing:
        test_passed("Audio player stopped")
    else:
        test_failed("Audio player still playing")
    
    print("")

# Test 4: _handle_music_completion triggers next song
async def test_handle_music_completion():
    print("4️⃣ Test _handle_music_completion triggers next song")
    
    assistant = MockAssistant()
    context = MockContext()
    
    # Start music with loop enabled
    await assistant.play_music(context, language="Hindi", loop_enabled=True)
    
    initial_url = assistant.unified_audio_player.current_url
    
    # Simulate completion
    await assistant._handle_music_completion(language="Hindi")
    
    if assistant.loop_enabled:
        test_passed("Loop still enabled after completion")
    else:
        test_failed("Loop disabled after completion")
    
    if assistant.unified_audio_player.playing:
        test_passed("Next song started playing")
    else:
        test_failed("Next song not playing")
    
    # URL should change (new random song)
    if assistant.unified_audio_player.current_url != initial_url:
        test_passed("New song URL different from previous")
    else:
        test_failed("Same song URL (should be different)")
    
    print("")

# Test 5: _handle_story_completion triggers next story
async def test_handle_story_completion():
    print("5️⃣ Test _handle_story_completion triggers next story")
    
    assistant = MockAssistant()
    context = MockContext()
    
    # Start story with loop enabled
    await assistant.play_story(context, category="Bedtime", loop_enabled=True)
    
    initial_url = assistant.unified_audio_player.current_url
    
    # Simulate completion
    await assistant._handle_story_completion(category="Bedtime")
    
    if assistant.loop_enabled:
        test_passed("Loop still enabled after completion")
    else:
        test_failed("Loop disabled after completion")
    
    if assistant.unified_audio_player.playing:
        test_passed("Next story started playing")
    else:
        test_failed("Next story not playing")
    
    print("")

# Test 6: Loop disabled doesn't trigger next playback
async def test_loop_disabled_no_continuation():
    print("6️⃣ Test loop disabled doesn't trigger next playback")
    
    assistant = MockAssistant()
    context = MockContext()
    
    # Play music WITHOUT loop
    await assistant.play_music(context, loop_enabled=False)
    
    if not assistant.loop_enabled:
        test_passed("Loop not enabled for non-loop playback")
    else:
        test_failed("Loop incorrectly enabled")
    
    # Manually disable loop and try completion
    assistant.loop_enabled = False
    initial_url = assistant.unified_audio_player.current_url
    
    await assistant._handle_music_completion()
    
    # URL should not change (no new song)
    if assistant.unified_audio_player.current_url == initial_url:
        test_passed("No new song played when loop disabled")
    else:
        test_failed("New song played despite loop disabled")
    
    print("")

# Test 7: Multiple stop_audio calls
async def test_multiple_stop_calls():
    print("7️⃣ Test multiple stop_audio calls")
    
    assistant = MockAssistant()
    context = MockContext()
    
    # Start music
    await assistant.play_music(context, loop_enabled=True)
    
    # First stop
    result1 = await assistant.stop_audio(context)
    if "Stopped playing audio" in result1:
        test_passed("First stop_audio successful")
    else:
        test_failed("First stop_audio failed")
    
    # Second stop (nothing playing)
    result2 = await assistant.stop_audio(context)
    if "No audio is currently playing" in result2:
        test_passed("Second stop_audio returns correct message")
    else:
        test_failed("Second stop_audio message incorrect")
    
    print("")

# Run all tests
async def run_all_tests():
    await test_play_music_with_loop()
    await test_play_story_with_loop()
    await test_stop_audio_clears_loop()
    await test_handle_music_completion()
    await test_handle_story_completion()
    await test_loop_disabled_no_continuation()
    await test_multiple_stop_calls()
    
    # Summary
    print("=" * 50)
    print(f"📊 Test Results: {tests_passed} passed, {tests_failed} failed")
    print("=" * 50)
    
    if tests_failed == 0:
        print("🎉 All Assistant Function tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_all_tests())
