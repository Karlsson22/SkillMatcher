package com.skillmatcher.service;

import com.skillmatcher.model.Job;
import com.skillmatcher.model.ExperienceLevel;
import com.skillmatcher.repository.JobRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Map;
import org.jsoup.Jsoup;
import org.jsoup.parser.Parser;

@Service
public class JobService {
    private final JobRepository jobRepository;
    private final JobAnalyzerService jobAnalyzerService;

    @Autowired
    public JobService(JobRepository jobRepository, JobAnalyzerService jobAnalyzerService) {
        this.jobRepository = jobRepository;
        this.jobAnalyzerService = jobAnalyzerService;
    }

    public Job saveJob(Job job) {
        // Sanitize the job description to remove HTML tags
        job.setDescription(stripHtmlTags(job.getDescription()));
        // Analyze the job before saving
        Map<String, Object> analysis = jobAnalyzerService.analyzeJob(job.getTitle(), job.getDescription());
        
        // Update job with analysis results
        job.setExperienceLevel((ExperienceLevel) analysis.get("experienceLevel"));
        job.setYearsOfExperience((List<Integer>) analysis.get("yearsOfExperience"));
        job.setMaxYearsRequired((Integer) analysis.get("minYearsRequired"));
        
        return jobRepository.save(job);
    }

    // Utility method to robustly strip HTML tags from a string using jsoup, handling double-encoded HTML
    private String stripHtmlTags(String input) {
        if (input == null) return null;
        String unescaped = Parser.unescapeEntities(input, true);
        String prev;
        String current = unescaped;
        do {
            prev = current;
            current = Jsoup.parse(prev).text().trim();
        } while (!current.equals(prev) && current.matches(".*<[^>]+>.*"));
        return current;
    }

    public List<Job> getAllJobs() {
        return jobRepository.findAll();
    }

    public List<Job> getJobsByExperienceLevel(ExperienceLevel experienceLevel) {
        return jobRepository.findByExperienceLevel(experienceLevel);
    }
} 