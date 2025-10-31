#!/usr/bin/env python3
"""
Simple Audio Test using OpenAI Whisper directly
This bypasses LiveKit audio buffer issues and tests STT directly
"""

import os
import asyncio
import wave
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

async def test_with_openai_whisper(audio_file_path: str):
    """Test audio file with OpenAI Whisper directly"""
    try:
        import openai
        
        # Get API key
        api_key = os.getenv('GROQ_API_KEY')  # Groq uses OpenAI-compatible API
        if not api_key:
            print("❌ GROQ_API_KEY not found")
            return None
        
        # Create OpenAI client pointing to Groq
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        
        print(f"🎤 Testing with Groq Whisper API...")
        
        # Open audio file
        with open(audio_file_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=audio_file,
                language="en"  # Using 'en' for compatibility
            )
        
        return transcript.text
        
    except Exception as e:
        print(f"❌ OpenAI Whisper test error: {e}")
        return None

async def test_with_aws_transcribe_direct(audio_file_path: str):
    """Test with AWS Transcribe using batch API"""
    try:
        import boto3
        import json
        import urllib.request
        import uuid
        import time
        
        # AWS credentials
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        
        if not aws_access_key_id or not aws_secret_access_key:
            print("❌ AWS credentials not found")
            return None
        
        print(f"🎤 Testing with AWS Transcribe batch API...")
        
        # Create AWS session
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
        
        # Create S3 and Transcribe clients
        s3_client = session.client('s3')
        transcribe_client = session.client('transcribe')
        
        # Create bucket name
        bucket_name = f"xiaozhi-transcribe-test-{aws_region}"
        
        # Try to create bucket if it doesn't exist
        try:
            s3_client.head_bucket(Bucket=bucket_name)
        except:
            try:
                if aws_region == 'us-east-1':
                    s3_client.create_bucket(Bucket=bucket_name)
                else:
                    s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': aws_region}
                    )
                print(f"✅ Created S3 bucket: {bucket_name}")
            except Exception as e:
                print(f"❌ Failed to create S3 bucket: {e}")
                return None
        
        # Upload audio file to S3
        s3_key = f"test-audio/{uuid.uuid4().hex}.wav"
        s3_client.upload_file(audio_file_path, bucket_name, s3_key)
        s3_uri = f"s3://{bucket_name}/{s3_key}"
        print(f"✅ Uploaded audio to S3: {s3_uri}")
        
        # Start transcription job
        job_name = f"test-job-{uuid.uuid4().hex}"
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': s3_uri},
            MediaFormat='wav',
            LanguageCode='en-IN',  # Indian English
            Settings={
                'ShowSpeakerLabels': False,
                'MaxSpeakerLabels': 1
            }
        )
        
        print(f"✅ Started transcription job: {job_name}")
        print(f"⏳ Waiting for completion...")
        
        # Wait for completion
        max_wait = 60  # 1 minute
        wait_time = 0
        
        while wait_time < max_wait:
            job_status = transcribe_client.get_transcription_job(
                TranscriptionJobName=job_name
            )
            
            status = job_status['TranscriptionJob']['TranscriptionJobStatus']
            
            if status == 'COMPLETED':
                # Get transcript
                transcript_uri = job_status['TranscriptionJob']['Transcript']['TranscriptFileUri']
                
                # Download transcript
                with urllib.request.urlopen(transcript_uri) as response:
                    transcript_data = json.loads(response.read().decode())
                
                # Extract text
                if 'results' in transcript_data and 'transcripts' in transcript_data['results']:
                    transcripts = transcript_data['results']['transcripts']
                    if transcripts and len(transcripts) > 0:
                        result_text = transcripts[0].get('transcript', '').strip()
                        
                        # Cleanup
                        try:
                            transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)
                            s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
                        except:
                            pass
                        
                        return result_text
                
                return None
                
            elif status == 'FAILED':
                print(f"❌ Transcription job failed")
                return None
            
            # Wait
            await asyncio.sleep(2)
            wait_time += 2
            print(f"⏳ Still waiting... ({wait_time}s)")
        
        print(f"❌ Transcription job timed out")
        return None
        
    except Exception as e:
        print(f"❌ AWS Transcribe direct test error: {e}")
        return None

def analyze_audio_file(audio_file_path: str):
    """Analyze the audio file"""
    try:
        with wave.open(audio_file_path, 'rb') as wav_file:
            frames = wav_file.getnframes()
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            duration = frames / sample_rate
            
        print(f"📊 Audio Analysis:")
        print(f"   File: {audio_file_path}")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Sample rate: {sample_rate} Hz")
        print(f"   Channels: {channels}")
        print(f"   Total frames: {frames}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing audio: {e}")
        return False

async def main():
    """Main test function"""
    audio_file = "hita3.wav"
    
    print("🎵 Simple Audio STT Test")
    print("=" * 40)
    
    # Check if file exists
    if not os.path.exists(audio_file):
        print(f"❌ Audio file not found: {audio_file}")
        return
    
    # Analyze audio
    if not analyze_audio_file(audio_file):
        return
    
    print(f"\n🧪 Testing STT Providers:")
    print("-" * 30)
    
    # Test 1: Groq Whisper (via OpenAI API)
    print(f"\n1. Testing Groq Whisper...")
    groq_result = await test_with_openai_whisper(audio_file)
    if groq_result:
        print(f"✅ Groq Result: \"{groq_result}\"")
    else:
        print(f"❌ Groq test failed")
    
    # Test 2: AWS Transcribe (batch API)
    print(f"\n2. Testing AWS Transcribe...")
    aws_result = await test_with_aws_transcribe_direct(audio_file)
    if aws_result:
        print(f"✅ AWS Result: \"{aws_result}\"")
    else:
        print(f"❌ AWS test failed")
    
    # Summary
    print(f"\n📝 Summary:")
    print(f"   Groq STT: {'✅ Working' if groq_result else '❌ Failed'}")
    print(f"   AWS STT: {'✅ Working' if aws_result else '❌ Failed'}")
    
    if groq_result or aws_result:
        print(f"\n🎉 At least one STT provider is working with your audio!")
    else:
        print(f"\n⚠️ Both STT providers failed. Check audio quality or API keys.")

if __name__ == "__main__":
    asyncio.run(main())