package com.skillmatcher.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.HashMap;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.io.File;
import com.skillmatcher.service.JobTechService;
import com.skillmatcher.service.JobService;
import org.springframework.beans.factory.annotation.Autowired;
import java.util.List;
import com.skillmatcher.model.JobTechJob;
import com.skillmatcher.model.Job;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.ArrayList;
import java.time.LocalDateTime;

@RestController
@RequestMapping("/api/jobs")
@CrossOrigin(origins = "http://localhost:3000")
public class JobScraperController {
    private static final Logger logger = LoggerFactory.getLogger(JobScraperController.class);
    
    @Autowired
    private JobTechService jobTechService;
    
    @Autowired
    private JobService jobService;
    
    private final ObjectMapper objectMapper = new ObjectMapper();

    @GetMapping("/scrape")
    public ResponseEntity<?> scrapeJobs(
            @RequestParam String keyword,
            @RequestParam String location,
            @RequestParam(required = false) Integer maxJobs,
            @RequestParam(required = false) Integer daysBack) {
        try {
            logger.info("Starting job scrape for keyword: {} and location: {} with maxJobs: {} and daysBack: {}", 
                keyword, location, maxJobs, daysBack);
            
            if (maxJobs != null) {
                jobTechService.setMaxJobsPerSource(maxJobs);
            }
            
            String scraperPath = "C:\\Users\\defau\\Cursor_Projekts\\SkillMatcher\\scraper\\job_scraper.py";
            
            logger.info("Using scraper at path: {}", scraperPath);
            
            ProcessBuilder processBuilder = new ProcessBuilder(
                "python",
                scraperPath,
                "--keyword", keyword,
                "--location", location
            );
            
            if (maxJobs != null) {
                processBuilder.command().add("--max-jobs");
                processBuilder.command().add(maxJobs.toString());
            }
            
            if (daysBack != null) {
                processBuilder.command().add("--days-back");
                processBuilder.command().add(daysBack.toString());
            }
            
            processBuilder.directory(new File("C:\\Users\\defau\\Cursor_Projekts\\SkillMatcher\\scraper"));
            
            Process process = processBuilder.start();
            
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            StringBuilder output = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append("\n");
                logger.info("Scraper output: {}", line);
            }
            
            BufferedReader errorReader = new BufferedReader(new InputStreamReader(process.getErrorStream()));
            StringBuilder errorOutput = new StringBuilder();
            while ((line = errorReader.readLine()) != null) {
                errorOutput.append(line).append("\n");
                logger.error("Scraper error: {}", line);
            }
            
            int exitCode = process.waitFor();
            logger.info("Scraper process exited with code: {}", exitCode);
            
            if (exitCode == 0) {
                File jsonFile = new File("C:\\Users\\defau\\Cursor_Projekts\\SkillMatcher\\scraper\\jobs.json");
                if (jsonFile.exists()) {
                    String jsonContent = new String(java.nio.file.Files.readAllBytes(jsonFile.toPath()));
                    logger.info("Successfully read jobs.json");
                    return ResponseEntity.ok(jsonContent);
                } else {
                    logger.error("jobs.json file not found at: {}", jsonFile.getAbsolutePath());
                    return ResponseEntity.badRequest().body("Failed to find jobs.json file");
                }
            }
            
            String errorMessage = "Failed to scrape jobs. Exit code: " + exitCode + 
                                "\nOutput: " + output.toString() + 
                                "\nError: " + errorOutput.toString();
            logger.error(errorMessage);
            return ResponseEntity.badRequest().body(errorMessage);
            
        } catch (Exception e) {
            logger.error("Exception during job scraping", e);
            return ResponseEntity.internalServerError().body("Error: " + e.getMessage());
        }
    }

    @GetMapping("/jobtech")
    public ResponseEntity<?> getJobTechJobs(
            @RequestParam String keyword,
            @RequestParam String location,
            @RequestParam(required = false) Integer maxJobs) {
        try {
            logger.info("Fetching jobs from JobTech API for keyword: {} and location: {} with maxJobs: {}", 
                keyword, location, maxJobs);
            
            if (maxJobs != null) {
                jobTechService.setMaxJobsPerSource(maxJobs);
            }
            
            List<JobTechJob> jobs = jobTechService.searchJobs(keyword, location);
            return ResponseEntity.ok(jobs);
        } catch (Exception e) {
            logger.error("Error fetching jobs from JobTech API", e);
            return ResponseEntity.internalServerError().body("Error: " + e.getMessage());
        }
    }

    @PostMapping("/analyze-and-save")
    public ResponseEntity<?> analyzeAndSaveJobs(
            @RequestParam String keyword,
            @RequestParam String location,
            @RequestParam(required = false) Integer maxJobs,
            @RequestParam(required = false) Integer daysBack) {
        try {
            logger.info("Starting job analysis and save for keyword: {} and location: {} with maxJobs: {} and daysBack: {}", 
                keyword, location, maxJobs, daysBack);
            
            List<Job> savedJobs = new ArrayList<>();
            
            if (maxJobs != null) {
                jobTechService.setMaxJobsPerSource(maxJobs);
            }
            
            ResponseEntity<?> scrapeResponse = scrapeJobs(keyword, location, maxJobs, daysBack);
            if (!scrapeResponse.getStatusCode().is2xxSuccessful()) {
                return scrapeResponse;
            }

            String jsonContent = (String) scrapeResponse.getBody();
            List<Map<String, Object>> jobsData = objectMapper.readValue(jsonContent, List.class);

            for (Map<String, Object> jobData : jobsData) {
                Job job = new Job();
                job.setTitle((String) jobData.get("title"));
                job.setCompany((String) jobData.get("company"));
                String jobLocation = (String) jobData.get("location");
                if (jobLocation == null || jobLocation.trim().isEmpty()) {
                    jobLocation = location; 
                }
                job.setLocation(jobLocation);
                job.setUrl((String) jobData.get("url"));
                job.setDescription(normalizeDescription((String) jobData.get("description")));
                job.setSource((String) jobData.get("source"));
                String uploadDate = (String) jobData.get("upload_date");
                if (uploadDate != null && !uploadDate.equals("N/A") && uploadDate.matches("\\d{4}-\\d{2}-\\d{2}")) {
                    job.setPostedDate(LocalDateTime.parse(uploadDate + "T00:00:00"));
                }
                job.setScrapedDate(LocalDateTime.now());
                String deadline = (String) jobData.get("deadline");
                if (deadline != null && !deadline.equals("N/A")) {
                    job.setDeadline(deadline);
                }
                savedJobs.add(jobService.saveJob(job));
                logger.info("Saved and analyzed job: {}", job.getTitle());
            }

            List<JobTechJob> jobTechJobs = jobTechService.searchJobs(keyword, location);
            for (JobTechJob jt : jobTechJobs) {
                Job job = new Job();
                job.setTitle(jt.getHeadline());
                job.setCompany(jt.getEmployer());
                String jobLocation = jt.getLocation();
                if (jobLocation == null || jobLocation.trim().isEmpty()) {
                    jobLocation = location; 
                }
                job.setLocation(jobLocation);
                job.setUrl(jt.getUrl());
                job.setDescription(normalizeDescription(jt.getDescription()));
                job.setSource("Arbetsformedlingen");
                String pubDate = jt.getPublicationDate();
                if (pubDate != null && pubDate.matches("\\d{4}-\\d{2}-\\d{2}")) {
                    job.setPostedDate(LocalDateTime.parse(pubDate + "T00:00:00"));
                }
                job.setScrapedDate(LocalDateTime.now());
                String deadline = jt.getApplicationDeadline();
                if (deadline != null && !deadline.equals("N/A")) {
                    job.setDeadline(deadline);
                }
                savedJobs.add(jobService.saveJob(job));
                logger.info("Saved and analyzed JobTech job: {}", job.getTitle());
            }

            return ResponseEntity.ok(savedJobs);
        } catch (Exception e) {
            logger.error("Error analyzing and saving jobs", e);
            return ResponseEntity.internalServerError().body("Error: " + e.getMessage());
        }
    }

    private String normalizeDescription(String description) {
        if (description == null) return null;
        String normalized = description.replace("\r\n", "\n").replace("\r", "\n");
        return normalized.trim();
    }

    @GetMapping("/all")
    public ResponseEntity<?> getAllJobs() {
        try {
            List<Job> jobs = jobService.getAllJobs();
            return ResponseEntity.ok(jobs);
        } catch (Exception e) {
            logger.error("Error fetching all jobs", e);
            return ResponseEntity.internalServerError().body("Error: " + e.getMessage());
        }
    }
} 