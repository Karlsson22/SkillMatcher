package com.skillmatcher.service;

import org.springframework.stereotype.Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;
import com.skillmatcher.model.ExperienceLevel;

@Service
public class JobAnalyzerService {
    private static final Logger logger = LoggerFactory.getLogger(JobAnalyzerService.class);

    // Experience level patterns
    private static final Pattern SENIOR_PATTERN = Pattern.compile(
        "\\b(senior|lead|principal|architect|expert|staff)\\b",
        Pattern.CASE_INSENSITIVE
    );

    private static final Pattern JUNIOR_PATTERN = Pattern.compile(
        "\\b(junior|entry|graduate|trainee|intern)\\b",
        Pattern.CASE_INSENSITIVE
    );

    private static final Pattern YEARS_EXPERIENCE_PATTERN = Pattern.compile(
        "\\b(?:minst|at least)?\\s*(\\d+|[a-ö]+)\\s*(?:years?|yrs?|års?)\\s*(?:of)?\\s*(?:experience|erfarenhet|arbetslivserfarenhet)\\b|" +
        "\\b(?:experience|erfarenhet|arbetslivserfarenhet)\\s*(?:of)?\\s*(?:minst|at least)?\\s*(\\d+|[a-ö]+)\\s*(?:years?|yrs?|års?)\\b|" +
        "\\b(?:minst|at least)\\s+(\\d+|[a-ö]+)\\s*(?:years?|yrs?|års?)\\s*(?:of)?\\s*(?:experience|erfarenhet|arbetslivserfarenhet)?\\b",
        Pattern.CASE_INSENSITIVE
    );

    private static final Map<String, Integer> SWEDISH_NUMBERS = new HashMap<>();
    static {
        SWEDISH_NUMBERS.put("ett", 1);
        SWEDISH_NUMBERS.put("två", 2);
        SWEDISH_NUMBERS.put("tre", 3);
        SWEDISH_NUMBERS.put("fyra", 4);
        SWEDISH_NUMBERS.put("fem", 5);
        SWEDISH_NUMBERS.put("sex", 6);
        SWEDISH_NUMBERS.put("sju", 7);
        SWEDISH_NUMBERS.put("åtta", 8);
        SWEDISH_NUMBERS.put("nio", 9);
        SWEDISH_NUMBERS.put("tio", 10);
    }

    private int parseSwedishNumber(String numberStr) {
        try {
            // First try to parse as a regular number
            return Integer.parseInt(numberStr);
        } catch (NumberFormatException e) {
            // If that fails, try to parse as a Swedish word
            String lowerNumber = numberStr.toLowerCase();
            return SWEDISH_NUMBERS.getOrDefault(lowerNumber, 0);
        }
    }

    public Map<String, Object> analyzeJob(String title, String description) {
        Map<String, Object> analysis = new HashMap<>();
        
        // Initialize experience level as NOT_SPECIFIED by default
        ExperienceLevel experienceLevel = ExperienceLevel.NOT_SPECIFIED;
        int minYearsRequired = 0;
        
        // Check title for senior/junior indicators
        boolean isSeniorTitle = SENIOR_PATTERN.matcher(title).find();
        boolean isJuniorTitle = JUNIOR_PATTERN.matcher(title).find();
        
        // Extract years of experience from description
        List<Integer> yearsOfExperience = new ArrayList<>();
        Matcher yearsMatcher = YEARS_EXPERIENCE_PATTERN.matcher(description);
        while (yearsMatcher.find()) {
            try {
                // Try group 1 first (direct number), then group 2 (after "minst/at least")
                String yearsStr = yearsMatcher.group(1) != null ? yearsMatcher.group(1) : yearsMatcher.group(2);
                int years = parseSwedishNumber(yearsStr);
                if (years > 0) {
                    yearsOfExperience.add(years);
                }
            } catch (Exception e) {
                logger.warn("Failed to parse years of experience: {}", yearsMatcher.group(0));
            }
        }
        
        // Set experience level based on title
        if (isSeniorTitle) {
            experienceLevel = ExperienceLevel.SENIOR;
            // Default to 5 years for senior positions unless description specifies otherwise
            minYearsRequired = 5;
        } else if (isJuniorTitle) {
            experienceLevel = ExperienceLevel.JUNIOR;
            // Don't set default years for junior positions
            minYearsRequired = 0;
        }
        
        // Update minimum years based on explicit requirements in description
        if (!yearsOfExperience.isEmpty()) {
            int maxYears = yearsOfExperience.stream().mapToInt(Integer::intValue).max().orElse(0);
            // Only update minYearsRequired if it's higher than the current value
            // This ensures senior title's 5-year default is only overridden by higher requirements
            if (maxYears > minYearsRequired) {
                minYearsRequired = maxYears;
            }
        }
        
        // Add analysis results
        analysis.put("experienceLevel", experienceLevel);
        analysis.put("yearsOfExperience", yearsOfExperience);
        analysis.put("minYearsRequired", minYearsRequired);
        analysis.put("hasSeniorTitle", isSeniorTitle);
        analysis.put("hasJuniorTitle", isJuniorTitle);
        
        return analysis;
    }
} 