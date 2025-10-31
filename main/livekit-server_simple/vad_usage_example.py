#!/usr/bin/env python3
"""
Example usage of the enhanced VAD analyzer with audio collection.

This shows how to integrate the VAD audio collection feature into your
existing LiveKit server implementation.
"""

import sys
import os
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vad.silero_onnx import SileroVADAnalyzer
from vad.vad_analyzer import VADParams, VADState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class EnhancedVADProcessor:
    """Example processor showing how to use the enhanced VAD with audio collection."""
    
    def __init__(self, model_path: str, sample_rate: int = 16000):
        """Initialize the VAD processor.
        
        Args:
            model_path: Path to the Silero VAD ONNX model
            sample_rate: Audio sample rate (8000 or 16000)
        """
        # Configure VAD parameters with audio collection
        self.vad_params = VADParams(
            confidence=0.5,           # Adjust based on your needs
            start_secs=0.2,          # Time to confirm speech start
            stop_secs=0.8,           # Time to confirm speech end
            min_volume=0.001,        # Minimum volume threshold
            save_audio=True,         # Enable audio collection
            audio_save_dir="vad_audio_captures"  # Directory for saved audio
        )
        
        # Initialize the VAD analyzer
        self.vad = SileroVADAnalyzer(
            model_path=model_path,
            sample_rate=sample_rate,
            params=self.vad_params
        )
        
        self.current_state = VADState.QUIET
        self.session_count = 0
        
        logging.info(f"VAD processor initialized with audio collection enabled")
        logging.info(f"Audio files will be saved to: {self.vad_params.audio_save_dir}")
    
    def process_audio_frame(self, audio_data: bytes) -> VADState:
        """Process an audio frame through the VAD.
        
        Args:
            audio_data: Raw audio bytes (16-bit PCM)
            
        Returns:
            Current VAD state
        """
        previous_state = self.current_state
        self.current_state = self.vad.analyze_audio(audio_data)
        
        # Log state changes
        if self.current_state != previous_state:
            logging.info(f"VAD state changed: {previous_state.name} -> {self.current_state.name}")
            
            if previous_state == VADState.QUIET and self.current_state == VADState.STARTING:
                self.session_count += 1
                logging.info(f"Started VAD session #{self.session_count} - Audio collection began")
            elif previous_state != VADState.QUIET and self.current_state == VADState.QUIET:
                logging.info(f"Ended VAD session #{self.session_count} - Audio saved to file")
        
        return self.current_state
    
    def is_speaking(self) -> bool:
        """Check if currently in a speaking state."""
        return self.current_state in [VADState.STARTING, VADState.SPEAKING, VADState.STOPPING]
    
    def reset(self):
        """Reset the VAD processor."""
        logging.info("Resetting VAD processor")
        self.vad.reset()
        self.current_state = VADState.QUIET
    
    def update_params(self, **kwargs):
        """Update VAD parameters dynamically.
        
        Example:
            processor.update_params(confidence=0.7, save_audio=False)
        """
        # Update the parameters
        for key, value in kwargs.items():
            if hasattr(self.vad_params, key):
                setattr(self.vad_params, key, value)
                logging.info(f"Updated VAD parameter {key} = {value}")
        
        # Apply the updated parameters
        self.vad.set_params(self.vad_params)


def example_usage():
    """Example of how to use the enhanced VAD processor."""
    
    # Path to your Silero VAD model
    model_path = "silero_vad.onnx"
    
    if not os.path.exists(model_path):
        print(f"Please download the Silero VAD model to: {model_path}")
        print("Download from: https://github.com/snakers4/silero-vad")
        return
    
    # Create the VAD processor
    processor = EnhancedVADProcessor(model_path, sample_rate=16000)
    
    # Example: Process audio frames in your LiveKit handler
    def on_audio_frame(audio_data: bytes):
        """Your audio frame handler."""
        vad_state = processor.process_audio_frame(audio_data)
        
        # Your existing logic here
        if processor.is_speaking():
            # Handle speech detection
            pass
        else:
            # Handle silence
            pass
    
    # Example: Update parameters during runtime
    processor.update_params(confidence=0.7)  # Make VAD more sensitive
    processor.update_params(save_audio=False)  # Disable audio saving
    
    print("VAD processor ready for use!")
    print("Audio collection is enabled - check the 'vad_audio_captures' directory")


if __name__ == "__main__":
    example_usage()