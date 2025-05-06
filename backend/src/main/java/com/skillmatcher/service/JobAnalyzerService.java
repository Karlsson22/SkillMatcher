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
        "\\b(\\d+)\\s*(?:years?|yrs?)\\s*(?:of)?\\s*experience\\b",
        Pattern.CASE_INSENSITIVE
    );

    public Map<String, Object> analyzeJob(String title, String description) {
        Map<String, Object> analysis = new HashMap<>();
        
        // Initialize experience level
        ExperienceLevel experienceLevel = ExperienceLevel.MID_LEVEL; // Default level
        int minYearsRequired = 0; // Default to 0 years
        
        // Check title for senior/junior indicators
        boolean isSeniorTitle = SENIOR_PATTERN.matcher(title).find();
        boolean isJuniorTitle = JUNIOR_PATTERN.matcher(title).find();
        
        if (isSeniorTitle) {
            experienceLevel = ExperienceLevel.SENIOR;
            minYearsRequired = 5; // Default for senior positions
        } else if (isJuniorTitle) {
            experienceLevel = ExperienceLevel.JUNIOR;
            minYearsRequired = 0; // Default for junior positions
        }
        
        // Extract years of experience from description
        List<Integer> yearsOfExperience = new ArrayList<>();
        Matcher yearsMatcher = YEARS_EXPERIENCE_PATTERN.matcher(description);
        while (yearsMatcher.find()) {
            try {
                int years = Integer.parseInt(yearsMatcher.group(1));
                yearsOfExperience.add(years);
            } catch (NumberFormatException e) {
                logger.warn("Failed to parse years of experience: {}", yearsMatcher.group(1));
            }
        }
        
        // Update experience level and minimum years based on explicit requirements
        if (!yearsOfExperience.isEmpty()) {
            int maxYears = yearsOfExperience.stream().mapToInt(Integer::intValue).max().orElse(0);
            minYearsRequired = maxYears; // Use the highest year requirement found
            
            // Update experience level based on years if not already determined by title
            if (!isSeniorTitle && !isJuniorTitle) {
                if (maxYears >= 5) {
                    experienceLevel = ExperienceLevel.SENIOR;
                } else if (maxYears <= 2) {
                    experienceLevel = ExperienceLevel.JUNIOR;
                }
            }
        }
        
        // Add analysis results
        analysis.put("experienceLevel", experienceLevel);
        analysis.put("yearsOfExperience", yearsOfExperience);
        analysis.put("minYearsRequired", minYearsRequired);
        
        // Add additional analysis results
        analysis.put("hasSeniorTitle", isSeniorTitle);
        analysis.put("hasJuniorTitle", isJuniorTitle);
        
        return analysis;
    }
} 