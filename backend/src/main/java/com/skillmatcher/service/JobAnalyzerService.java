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

    private static final Pattern SENIOR_PATTERN = Pattern.compile(
        "\\b(senior|lead|principal|architect|expert|staff)\\b",
        Pattern.CASE_INSENSITIVE
    );

    private static final Pattern JUNIOR_PATTERN = Pattern.compile(
        "\\b(junior|entry|graduate|trainee|intern)\\b",
        Pattern.CASE_INSENSITIVE
    );

    private static final Pattern YEARS_EXPERIENCE_PATTERN = Pattern.compile(
        "\\b(?:minst|at least)?\\s*(\\d+)(?:\\s*[+-]|\\s*-\\s*(\\d+))?\\s*(?:years?|yrs?|års?)\\s*(?:of)?\\s*(?:experience|erfarenhet|arbetslivserfarenhet)\\b|" +
        "\\b(?:experience|erfarenhet|arbetslivserfarenhet)\\s*(?:of)?\\s*(?:minst|at least)?\\s*(\\d+)(?:\\s*[+-]|\\s*-\\s*(\\d+))?\\s*(?:years?|yrs?|års?)\\b|" +
        "\\b(?:minst|at least)\\s+(\\d+)(?:\\s*[+-]|\\s*-\\s*(\\d+))?\\s*(?:years?|yrs?|års?)\\s*(?:of)?\\s*(?:experience|erfarenhet|arbetslivserfarenhet)?\\b|" +
        "\\b(?:några|flera|ett par)\\s*(?:years?|yrs?|års?)\\s*(?:of)?\\s*(?:experience|erfarenhet|arbetslivserfarenhet)\\b",
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
        SWEDISH_NUMBERS.put("några", 1);
        SWEDISH_NUMBERS.put("flera", 2);
        SWEDISH_NUMBERS.put("ett par", 1);
    }

    private int parseSwedishNumber(String numberStr) {
        if (numberStr == null) return 0;
        
        try {
            return Integer.parseInt(numberStr);
        } catch (NumberFormatException e) {
            String lowerNumber = numberStr.toLowerCase();
            return SWEDISH_NUMBERS.getOrDefault(lowerNumber, 0);
        }
    }

    public Map<String, Object> analyzeJob(String title, String description) {
        Map<String, Object> analysis = new HashMap<>();
        
        ExperienceLevel experienceLevel = ExperienceLevel.NOT_SPECIFIED;
        int minYearsRequired = 0;
        
        boolean isSeniorTitle = SENIOR_PATTERN.matcher(title).find();
        boolean isJuniorTitle = JUNIOR_PATTERN.matcher(title).find();
        
        List<Integer> yearsOfExperience = new ArrayList<>();
        Matcher yearsMatcher = YEARS_EXPERIENCE_PATTERN.matcher(description);
        while (yearsMatcher.find()) {
            try {
                Integer found = null;
                for (int i = 1; i <= yearsMatcher.groupCount(); i += 2) {
                    String first = yearsMatcher.group(i);
                    String second = (i + 1 <= yearsMatcher.groupCount()) ? yearsMatcher.group(i + 1) : null;
                    if (first != null) {
                        int firstNum = parseSwedishNumber(first);
                        String match = yearsMatcher.group(0).toLowerCase();
                        if (match.contains("+") || (second != null && match.contains("-"))) {
                            found = firstNum;
                        } else if (second != null) {
                            int secondNum = parseSwedishNumber(second);
                            found = Math.min(firstNum, secondNum);
                        } else {
                            found = firstNum;
                        }
                        break;
                    }
                }
                if (found != null && found > 0) {
                    yearsOfExperience.add(found);
                } else {
                    String match = yearsMatcher.group(0).toLowerCase();
                    if (match.contains("några") || match.contains("ett par")) {
                        yearsOfExperience.add(1);
                    } else if (match.contains("flera")) {
                        yearsOfExperience.add(2);
                    }
                }
            } catch (Exception e) {
                logger.warn("Failed to parse years of experience: {}", yearsMatcher.group(0));
            }
        }
        
        if (isSeniorTitle) {
            experienceLevel = ExperienceLevel.SENIOR;
            minYearsRequired = 5;
        } else if (isJuniorTitle) {
            experienceLevel = ExperienceLevel.JUNIOR;
            minYearsRequired = 0;
        }
        
        if (!yearsOfExperience.isEmpty()) {
            int minYears = yearsOfExperience.stream().mapToInt(Integer::intValue).min().orElse(0);
            if (minYears > minYearsRequired) {
                minYearsRequired = minYears;
            }
        }
        
        analysis.put("experienceLevel", experienceLevel);
        analysis.put("yearsOfExperience", yearsOfExperience);
        analysis.put("minYearsRequired", minYearsRequired);
        analysis.put("hasSeniorTitle", isSeniorTitle);
        analysis.put("hasJuniorTitle", isJuniorTitle);
        
        return analysis;
    }
} 