package xiaozhi.modules.rag.agent;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import xiaozhi.modules.rag.service.VectorProcessingService;

import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.util.ArrayList;
import java.util.regex.Pattern;
import java.util.regex.Matcher;

/**
 * Mathematics Agent for Standard 6
 * Specialized agent for handling mathematical queries with educational context
 * Provides step-by-step solutions and age-appropriate explanations
 * 
 * @author Claude  
 * @since 1.0.0
 */
@Slf4j
@Component
public class MathematicsAgent {
    
    @Autowired
    private VectorProcessingService vectorProcessingService;
    
    // Mathematical patterns for query analysis
    private static final Pattern NUMBER_PATTERN = Pattern.compile("\\b\\d+(\\.\\d+)?\\b");
    private static final Pattern FRACTION_PATTERN = Pattern.compile("\\b\\d+/\\d+\\b");
    private static final Pattern OPERATION_PATTERN = Pattern.compile("[+\\-×÷=]");
    private static final Pattern GEOMETRY_PATTERN = Pattern.compile("(?i)(angle|triangle|square|rectangle|circle|perimeter|area)");
    
    // Subject-specific keywords
    private static final String[] MATH_CONCEPTS = {
        "patterns", "numbers", "addition", "subtraction", "multiplication", "division",
        "factors", "multiples", "prime", "composite", "fractions", "decimals",
        "geometry", "angles", "lines", "perimeter", "area", "symmetry",
        "data", "graph", "pictograph", "integers", "negative numbers",
        "constructions", "measurement"
    };
    
    /**
     * Process mathematical query with educational context
     */
    public Map<String, Object> processQuery(String query, Map<String, Object> context) {
        try {
            log.info("Processing mathematics query: {}", query);
            
            // Analyze query type and mathematical content
            Map<String, Object> queryAnalysis = analyzeQuery(query);
            
            // Search for relevant content
            List<Map<String, Object>> relevantContent = searchRelevantContent(query, context);
            
            // Generate mathematical response
            Map<String, Object> response = generateMathematicalResponse(query, queryAnalysis, relevantContent, context);
            
            // Enhance with educational features
            enhanceEducationalResponse(response, queryAnalysis);
            
            log.info("Successfully processed mathematics query with {} relevant sources", 
                    relevantContent.size());
            
            return response;
            
        } catch (Exception e) {
            log.error("Error processing mathematics query: {}", query, e);
            return createErrorResponse("Failed to process mathematical query", e.getMessage());
        }
    }
    
    /**
     * Analyze query to determine mathematical concepts and difficulty
     */
    private Map<String, Object> analyzeQuery(String query) {
        Map<String, Object> analysis = new HashMap<>();
        String lowerQuery = query.toLowerCase();
        
        // Determine query type
        String queryType = determineQueryType(lowerQuery);
        analysis.put("query_type", queryType);
        
        // Extract mathematical elements
        List<String> numbers = extractNumbers(query);
        List<String> operations = extractOperations(query);
        List<String> concepts = extractConcepts(lowerQuery);
        
        analysis.put("numbers", numbers);
        analysis.put("operations", operations);
        analysis.put("concepts", concepts);
        
        // Determine complexity level
        String complexityLevel = determineComplexity(queryType, numbers, operations, concepts);
        analysis.put("complexity_level", complexityLevel);
        
        // Identify chapter/topic area
        String topicArea = identifyTopicArea(concepts, lowerQuery);
        analysis.put("topic_area", topicArea);
        
        // Check if step-by-step solution is needed
        boolean needsSteps = needsStepByStepSolution(queryType, lowerQuery);
        analysis.put("needs_steps", needsSteps);
        
        log.debug("Query analysis completed: {}", analysis);
        return analysis;
    }
    
    /**
     * Determine the type of mathematical query
     */
    private String determineQueryType(String query) {
        if (query.contains("what is") || query.contains("define") || query.contains("explain")) {
            return "definition";
        } else if (query.contains("how to") || query.contains("solve") || query.contains("calculate")) {
            return "procedure";
        } else if (query.contains("example") || query.contains("show me")) {
            return "example";
        } else if (OPERATION_PATTERN.matcher(query).find()) {
            return "calculation";
        } else if (query.contains("difference") || query.contains("compare")) {
            return "comparison";
        } else {
            return "general";
        }
    }
    
    /**
     * Extract numbers from query
     */
    private List<String> extractNumbers(String query) {
        List<String> numbers = new ArrayList<>();
        Matcher matcher = NUMBER_PATTERN.matcher(query);
        
        while (matcher.find()) {
            numbers.add(matcher.group());
        }
        
        // Also look for fractions
        Matcher fractionMatcher = FRACTION_PATTERN.matcher(query);
        while (fractionMatcher.find()) {
            numbers.add(fractionMatcher.group());
        }
        
        return numbers;
    }
    
    /**
     * Extract mathematical operations
     */
    private List<String> extractOperations(String query) {
        List<String> operations = new ArrayList<>();
        
        if (query.contains("add") || query.contains("+")) operations.add("addition");
        if (query.contains("subtract") || query.contains("-")) operations.add("subtraction");  
        if (query.contains("multiply") || query.contains("×") || query.contains("*")) operations.add("multiplication");
        if (query.contains("divide") || query.contains("÷") || query.contains("/")) operations.add("division");
        
        return operations;
    }
    
    /**
     * Extract mathematical concepts from query
     */
    private List<String> extractConcepts(String query) {
        List<String> concepts = new ArrayList<>();
        
        for (String concept : MATH_CONCEPTS) {
            if (query.contains(concept)) {
                concepts.add(concept);
            }
        }
        
        return concepts;
    }
    
    /**
     * Determine complexity level of the query
     */
    private String determineComplexity(String queryType, List<String> numbers, 
                                     List<String> operations, List<String> concepts) {
        if (numbers.size() > 2 || operations.size() > 2) {
            return "advanced";
        } else if (numbers.size() > 0 || operations.size() > 0 || 
                  concepts.stream().anyMatch(c -> c.contains("fraction") || c.contains("decimal"))) {
            return "intermediate";
        } else {
            return "basic";
        }
    }
    
    /**
     * Identify the topic area/chapter
     */
    private String identifyTopicArea(List<String> concepts, String query) {
        if (concepts.contains("patterns") || query.contains("pattern")) {
            return "Chapter 1: Patterns in Mathematics";
        } else if (concepts.contains("lines") || concepts.contains("angles")) {
            return "Chapter 2: Lines and Angles";
        } else if (concepts.contains("factors") || concepts.contains("multiples") || concepts.contains("prime")) {
            return "Chapter 3: Number Play";
        } else if (concepts.contains("data") || concepts.contains("graph")) {
            return "Chapter 4: Data Handling and Presentation";
        } else if (concepts.contains("prime") && query.contains("factorization")) {
            return "Chapter 5: Prime Time";
        } else if (concepts.contains("perimeter") || concepts.contains("area")) {
            return "Chapter 6: Perimeter and Area";
        } else if (concepts.contains("fractions")) {
            return "Chapter 7: Fractions";
        } else if (concepts.contains("constructions")) {
            return "Chapter 8: Playing with Constructions";
        } else if (concepts.contains("symmetry")) {
            return "Chapter 9: Symmetry";
        } else if (concepts.contains("integers") || concepts.contains("negative")) {
            return "Chapter 10: The Other Side of Zero";
        } else {
            return "General Mathematics";
        }
    }
    
    /**
     * Check if query needs step-by-step solution
     */
    private boolean needsStepByStepSolution(String queryType, String query) {
        return queryType.equals("procedure") || queryType.equals("calculation") ||
               query.contains("step") || query.contains("solve") || query.contains("how to");
    }
    
    /**
     * Search for relevant educational content
     */
    private List<Map<String, Object>> searchRelevantContent(String query, Map<String, Object> context) {
        try {
            // Use vector search to find relevant content
            String collectionName = "math_std6_mathematics";
            Map<String, Object> filters = new HashMap<>();
            
            // Add context-based filters
            if (context.containsKey("difficulty_level")) {
                filters.put("difficulty_level", context.get("difficulty_level"));
            }
            
            // Search using vector processing service
            List<Map<String, Object>> results = vectorProcessingService.searchSimilarContent(
                query, collectionName, filters, 5, 0.7f
            ).join();
            
            log.debug("Found {} relevant content pieces for query", results.size());
            return results;
            
        } catch (Exception e) {
            log.warn("Error searching relevant content: {}", e.getMessage());
            return new ArrayList<>();
        }
    }
    
    /**
     * Generate comprehensive mathematical response
     */
    private Map<String, Object> generateMathematicalResponse(String query, Map<String, Object> analysis,
                                                           List<Map<String, Object>> relevantContent,
                                                           Map<String, Object> context) {
        Map<String, Object> response = new HashMap<>();
        
        String queryType = (String) analysis.get("query_type");
        String complexityLevel = (String) analysis.get("complexity_level");
        boolean needsSteps = (Boolean) analysis.get("needs_steps");
        
        // Generate main response based on query type
        String mainResponse = generateMainResponse(query, queryType, analysis, relevantContent);
        response.put("main_response", mainResponse);
        
        // Add step-by-step solution if needed
        if (needsSteps) {
            List<String> steps = generateStepByStepSolution(query, analysis, relevantContent);
            response.put("step_by_step", steps);
        }
        
        // Add examples if helpful
        List<Map<String, Object>> examples = generateExamples(query, analysis, relevantContent);
        if (!examples.isEmpty()) {
            response.put("examples", examples);
        }
        
        // Add practice suggestions
        List<String> practice = generatePracticeSuggestions(query, analysis);
        response.put("practice_suggestions", practice);
        
        // Add related concepts
        List<String> relatedConcepts = generateRelatedConcepts(analysis, relevantContent);
        response.put("related_concepts", relatedConcepts);
        
        return response;
    }
    
    /**
     * Generate the main response text
     */
    private String generateMainResponse(String query, String queryType, Map<String, Object> analysis,
                                      List<Map<String, Object>> relevantContent) {
        
        String topicArea = (String) analysis.get("topic_area");
        @SuppressWarnings("unchecked")
        List<String> concepts = (List<String>) analysis.get("concepts");
        
        StringBuilder response = new StringBuilder();
        
        // Start with topic context
        if (!topicArea.equals("General Mathematics")) {
            response.append("This question is from ").append(topicArea).append(".\n\n");
        }
        
        // Generate response based on query type
        switch (queryType) {
            case "definition":
                response.append(generateDefinitionResponse(concepts, relevantContent));
                break;
            case "procedure":
                response.append(generateProcedureResponse(query, analysis));
                break;
            case "calculation":
                response.append(generateCalculationResponse(query, analysis));
                break;
            case "example":
                response.append(generateExampleResponse(concepts, relevantContent));
                break;
            default:
                response.append(generateGeneralResponse(query, concepts, relevantContent));
        }
        
        return response.toString();
    }
    
    /**
     * Generate definition-type response
     */
    private String generateDefinitionResponse(List<String> concepts, List<Map<String, Object>> relevantContent) {
        if (concepts.isEmpty()) {
            return "Let me explain this mathematical concept in simple terms suitable for Class 6 students.";
        }
        
        String mainConcept = concepts.get(0);
        
        // Generate age-appropriate definitions
        switch (mainConcept) {
            case "prime":
                return "A prime number is a special number that has exactly two factors: 1 and itself. For example, 7 is prime because only 1 and 7 can divide it evenly. The smallest prime number is 2.";
            case "factors":
                return "Factors of a number are the numbers that divide it completely without leaving a remainder. For example, the factors of 12 are 1, 2, 3, 4, 6, and 12.";
            case "fractions":
                return "A fraction represents a part of a whole. The top number (numerator) tells us how many parts we have, and the bottom number (denominator) tells us how many equal parts the whole is divided into.";
            case "perimeter":
                return "Perimeter is the distance around the outside of a shape. To find it, we add up all the sides of the shape.";
            case "area":
                return "Area is the amount of space inside a shape. We measure it in square units like square centimeters (cm²).";
            default:
                return "This is an important mathematical concept that helps us understand numbers and shapes better.";
        }
    }
    
    /**
     * Generate procedure-type response
     */
    private String generateProcedureResponse(String query, Map<String, Object> analysis) {
        @SuppressWarnings("unchecked")
        List<String> concepts = (List<String>) analysis.get("concepts");
        
        if (concepts.contains("fractions")) {
            return "To work with fractions, follow these simple steps:\n1. Understand what the numerator (top) and denominator (bottom) mean\n2. Make sure denominators are the same for addition/subtraction\n3. Add or subtract only the numerators\n4. Simplify your answer if possible";
        } else if (concepts.contains("perimeter")) {
            return "To find the perimeter:\n1. Identify all the sides of the shape\n2. Add up the lengths of all sides\n3. Write your answer with proper units (cm, m, etc.)";
        } else {
            return "Here's how to solve this step by step in a way that's easy for Class 6 students to understand.";
        }
    }
    
    /**
     * Generate calculation-type response
     */
    private String generateCalculationResponse(String query, Map<String, Object> analysis) {
        return "Let me show you how to calculate this step by step, making sure each step is clear and easy to follow.";
    }
    
    /**
     * Generate example-type response
     */
    private String generateExampleResponse(List<String> concepts, List<Map<String, Object>> relevantContent) {
        return "Here are some clear examples that will help you understand this concept better:";
    }
    
    /**
     * Generate general response
     */
    private String generateGeneralResponse(String query, List<String> concepts, List<Map<String, Object>> relevantContent) {
        return "This is a great mathematical question! Let me help you understand this concept clearly.";
    }
    
    /**
     * Generate step-by-step solution
     */
    private List<String> generateStepByStepSolution(String query, Map<String, Object> analysis,
                                                   List<Map<String, Object>> relevantContent) {
        List<String> steps = new ArrayList<>();
        
        @SuppressWarnings("unchecked")
        List<String> concepts = (List<String>) analysis.get("concepts");
        String queryType = (String) analysis.get("query_type");
        
        if (concepts.contains("fractions") && queryType.equals("calculation")) {
            steps.add("Step 1: Look at the denominators (bottom numbers) of the fractions");
            steps.add("Step 2: If denominators are the same, add/subtract the numerators (top numbers)");
            steps.add("Step 3: If denominators are different, find equivalent fractions with same denominators");
            steps.add("Step 4: Perform the operation and simplify if needed");
        } else if (concepts.contains("perimeter")) {
            steps.add("Step 1: Identify the shape and all its sides");
            steps.add("Step 2: Write down the length of each side");
            steps.add("Step 3: Add all the side lengths together");
            steps.add("Step 4: Write the answer with correct units");
        } else {
            steps.add("Step 1: Read the problem carefully and identify what is given");
            steps.add("Step 2: Understand what needs to be found");
            steps.add("Step 3: Choose the right method or formula");
            steps.add("Step 4: Solve step by step");
            steps.add("Step 5: Check your answer");
        }
        
        return steps;
    }
    
    /**
     * Generate relevant examples
     */
    private List<Map<String, Object>> generateExamples(String query, Map<String, Object> analysis,
                                                      List<Map<String, Object>> relevantContent) {
        List<Map<String, Object>> examples = new ArrayList<>();
        
        @SuppressWarnings("unchecked")
        List<String> concepts = (List<String>) analysis.get("concepts");
        
        if (concepts.contains("prime")) {
            examples.add(Map.of(
                "title", "Prime Number Example",
                "problem", "Is 17 a prime number?",
                "solution", "Check: 17 ÷ 1 = 17, 17 ÷ 17 = 1. Only 1 and 17 divide 17 evenly. So 17 is prime!",
                "difficulty", "basic"
            ));
        }
        
        if (concepts.contains("fractions")) {
            examples.add(Map.of(
                "title", "Adding Fractions",
                "problem", "Add 1/4 + 2/4",
                "solution", "Since denominators are same: 1/4 + 2/4 = (1+2)/4 = 3/4",
                "difficulty", "basic"
            ));
        }
        
        return examples;
    }
    
    /**
     * Generate practice suggestions
     */
    private List<String> generatePracticeSuggestions(String query, Map<String, Object> analysis) {
        List<String> suggestions = new ArrayList<>();
        
        @SuppressWarnings("unchecked")
        List<String> concepts = (List<String>) analysis.get("concepts");
        String topicArea = (String) analysis.get("topic_area");
        
        suggestions.add("Practice with similar problems from " + topicArea);
        suggestions.add("Try the exercises in your textbook for this chapter");
        
        if (concepts.contains("fractions")) {
            suggestions.add("Practice adding fractions with same denominators first");
            suggestions.add("Draw pictures to visualize fraction problems");
        } else if (concepts.contains("geometry")) {
            suggestions.add("Draw and measure different shapes to understand better");
            suggestions.add("Look for geometric shapes in your surroundings");
        }
        
        suggestions.add("Ask questions if anything is unclear - mathematics builds on previous knowledge!");
        
        return suggestions;
    }
    
    /**
     * Generate related concepts
     */
    private List<String> generateRelatedConcepts(Map<String, Object> analysis, List<Map<String, Object>> relevantContent) {
        List<String> related = new ArrayList<>();
        
        @SuppressWarnings("unchecked")
        List<String> concepts = (List<String>) analysis.get("concepts");
        
        if (concepts.contains("prime")) {
            related.add("Composite numbers");
            related.add("Factors and multiples");
            related.add("Prime factorization");
        } else if (concepts.contains("fractions")) {
            related.add("Equivalent fractions");
            related.add("Mixed numbers");
            related.add("Decimal numbers");
        } else if (concepts.contains("perimeter")) {
            related.add("Area calculation");
            related.add("Different shapes");
            related.add("Measurement units");
        }
        
        return related;
    }
    
    /**
     * Enhance response with educational features
     */
    private void enhanceEducationalResponse(Map<String, Object> response, Map<String, Object> analysis) {
        // Add metadata for educational tracking
        response.put("educational_metadata", Map.of(
            "subject", "Mathematics",
            "standard", 6,
            "topic_area", analysis.get("topic_area"),
            "complexity_level", analysis.get("complexity_level"),
            "age_group", "11-12 years",
            "pedagogical_approach", "step-by-step, visual, age-appropriate"
        ));
        
        // Add encouragement for students
        response.put("encouragement", generateEncouragement(analysis));
        
        // Add tips for better understanding
        response.put("learning_tips", generateLearningTips(analysis));
    }
    
    /**
     * Generate encouraging message for students
     */
    private String generateEncouragement(Map<String, Object> analysis) {
        String complexityLevel = (String) analysis.get("complexity_level");
        
        switch (complexityLevel) {
            case "basic":
                return "Great question! You're building a strong foundation in mathematics. Keep practicing!";
            case "intermediate": 
                return "This is a good challenge! Take your time to understand each step. You're doing well!";
            case "advanced":
                return "Excellent! You're tackling advanced concepts. Remember, every expert was once a beginner!";
            default:
                return "Mathematics is all about practice and patience. You're on the right track!";
        }
    }
    
    /**
     * Generate learning tips
     */
    private List<String> generateLearningTips(Map<String, Object> analysis) {
        List<String> tips = new ArrayList<>();
        
        tips.add("Always read the problem twice to understand what's being asked");
        tips.add("Write down what you know and what you need to find");
        tips.add("Check your answer by working backwards or using a different method");
        
        @SuppressWarnings("unchecked")
        List<String> concepts = (List<String>) analysis.get("concepts");
        
        if (concepts.contains("fractions")) {
            tips.add("Draw pictures or use objects to visualize fraction problems");
        } else if (concepts.contains("geometry")) {
            tips.add("Draw diagrams to help visualize geometric problems");
        }
        
        return tips;
    }
    
    /**
     * Create error response
     */
    private Map<String, Object> createErrorResponse(String message, String details) {
        Map<String, Object> errorResponse = new HashMap<>();
        errorResponse.put("status", "error");
        errorResponse.put("message", message);
        errorResponse.put("details", details);
        errorResponse.put("main_response", "I'm sorry, I had trouble processing your mathematical question. Please try rephrasing it or ask me something else about Class 6 Mathematics!");
        return errorResponse;
    }
}