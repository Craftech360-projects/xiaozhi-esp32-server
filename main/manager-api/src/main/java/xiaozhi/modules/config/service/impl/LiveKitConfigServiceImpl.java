package xiaozhi.modules.config.service.impl;

import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import xiaozhi.modules.config.service.LiveKitConfigService;
import xiaozhi.modules.model.service.ModelConfigService;
import xiaozhi.modules.model.entity.ModelConfigEntity;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.HashMap;
import java.util.Map;
import java.util.List;

@Slf4j
@Service
@AllArgsConstructor
public class LiveKitConfigServiceImpl implements LiveKitConfigService {

    private final ModelConfigService modelConfigService;

    @Override
    public Map<String, Object> getCurrentConfig() {
        Map<String, Object> config = new HashMap<>();

        try {
            // Call Python script to get current config
            String scriptPath = "../livekit-server/sync_config.py";
            ProcessBuilder pb = new ProcessBuilder("python", scriptPath, "--get-config");
            pb.directory(new java.io.File("../livekit-server"));

            Process process = pb.start();
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));

            String line;
            while ((line = reader.readLine()) != null) {
                if (line.startsWith("CONFIG:")) {
                    // Parse the config line if needed
                    log.info("Current config: {}", line);
                }
            }

            process.waitFor();

        } catch (Exception e) {
            log.error("Error getting current config", e);
        }

        return config;
    }

    @Override
    public Map<String, Object> syncToLiveKit() {
        Map<String, Object> result = new HashMap<>();

        try {
            // Call Python sync script
            String scriptPath = "../livekit-server/sync_config.py";
            ProcessBuilder pb = new ProcessBuilder("python", scriptPath);
            pb.directory(new java.io.File("../livekit-server"));

            Process process = pb.start();

            // Read output
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            StringBuilder output = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append("\n");
            }

            int exitCode = process.waitFor();

            result.put("success", exitCode == 0);
            result.put("output", output.toString());

            if (exitCode == 0) {
                log.info("LiveKit configuration synced successfully");
            } else {
                log.error("LiveKit configuration sync failed with exit code: {}", exitCode);
            }

        } catch (Exception e) {
            log.error("Error syncing to LiveKit", e);
            result.put("success", false);
            result.put("error", e.getMessage());
        }

        return result;
    }

    @Override
    public void notifyConfigChange() {
        // This could trigger WebSocket notification or other real-time updates
        log.info("Configuration change notification sent");
    }

    @Override
    public Map<String, Object> getDefaultModels() {
        Map<String, Object> models = new HashMap<>();

        try {
            // Model type mapping for database query and API response
            Map<String, String> modelMapping = new HashMap<>();
            modelMapping.put("GroqLLM", "llama-3.1-8b-instant");
            modelMapping.put("GeminiLLM", "gemini-1.5-flash");
            modelMapping.put("GroqASR", "whisper-large-v3-turbo");
            modelMapping.put("OpenaiASR", "whisper-1");
            modelMapping.put("ElevenLabs", "eleven_turbo_v2_5");
            modelMapping.put("EdgeTTS", "edge-tts");
            modelMapping.put("openai", "tts-1");
            modelMapping.put("gemini", "gemini-tts");

            // Get default models for each type
            String[] modelTypes = {"llm", "tts", "asr"};

            for (String modelType : modelTypes) {
                // Get models from database, prioritizing Groq models
                List<ModelConfigEntity> modelList = modelConfigService.getEnabledModelsByType(modelType);

                ModelConfigEntity selectedModel = null;

                // First priority: Groq models
                for (ModelConfigEntity model : modelList) {
                    if (model.getModelCode().contains("Groq")) {
                        selectedModel = model;
                        break;
                    }
                }

                // Second priority: Default models
                if (selectedModel == null) {
                    for (ModelConfigEntity model : modelList) {
                        if (model.getIsDefault() == 1) {
                            selectedModel = model;
                            break;
                        }
                    }
                }

                // Third priority: First available
                if (selectedModel == null && !modelList.isEmpty()) {
                    selectedModel = modelList.get(0);
                }

                if (selectedModel != null) {
                    String modelCode = selectedModel.getModelCode();
                    String mappedModel = modelMapping.getOrDefault(modelCode, modelCode);

                    if ("llm".equals(modelType)) {
                        models.put("LLM_MODEL", mappedModel);
                        models.put("llm_name", selectedModel.getModelName());
                        models.put("llm_code", modelCode);
                    } else if ("asr".equals(modelType)) {
                        models.put("STT_MODEL", mappedModel);
                        models.put("stt_name", selectedModel.getModelName());
                        models.put("stt_code", modelCode);
                    } else if ("tts".equals(modelType)) {
                        models.put("TTS_MODEL", mappedModel);
                        models.put("tts_name", selectedModel.getModelName());
                        models.put("tts_code", modelCode);

                        // Set TTS provider based on model
                        String provider = "edge"; // safe default
                        if ("ElevenLabs".equals(modelCode)) {
                            provider = "elevenlabs";
                        } else if ("EdgeTTS".equals(modelCode)) {
                            provider = "edge";
                        } else if ("openai".equals(modelCode)) {
                            provider = "openai";
                        } else if ("gemini".equals(modelCode)) {
                            provider = "gemini";
                        }
                        models.put("TTS_PROVIDER", provider);
                    }
                }
            }

            log.info("Retrieved default models from database: {}", models);

        } catch (Exception e) {
            log.error("Error getting default models from database", e);
        }

        return models;
    }
}