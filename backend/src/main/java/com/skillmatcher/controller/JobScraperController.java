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
import org.springframework.beans.factory.annotation.Autowired;
import java.util.List;
import com.skillmatcher.model.JobTechJob;

@RestController
@RequestMapping("/api/jobs")
@CrossOrigin(origins = "http://localhost:3000")
public class JobScraperController {
    private static final Logger logger = LoggerFactory.getLogger(JobScraperController.class);
    
    @Autowired
    private JobTechService jobTechService;

    @GetMapping("/scrape")
    public ResponseEntity<?> scrapeJobs(
            @RequestParam String keyword,
            @RequestParam String location,
            @RequestParam(required = false) Integer maxJobs,
            @RequestParam(required = false) Integer daysBack) {
        try {
            logger.info("Starting job scrape for keyword: {} and location: {} with maxJobs: {} and daysBack: {}", 
                keyword, location, maxJobs, daysBack);
            
            // Use absolute path to the scraper directory
            String scraperPath = "C:\\Users\\defau\\Cursor_Projekts\\SkillMatcher\\scraper\\job_scraper.py";
            
            logger.info("Using scraper at path: {}", scraperPath);
            
            // Build the command to run the Python script
            ProcessBuilder processBuilder = new ProcessBuilder(
                "python",
                scraperPath,
                "--keyword", keyword,
                "--location", location
            );
            
            // Add optional parameters if they are provided
            if (maxJobs != null) {
                processBuilder.command().add("--max-jobs");
                processBuilder.command().add(maxJobs.toString());
            }
            
            if (daysBack != null) {
                processBuilder.command().add("--days-back");
                processBuilder.command().add(daysBack.toString());
            }
            
            // Set the working directory to the scraper directory
            processBuilder.directory(new File("C:\\Users\\defau\\Cursor_Projekts\\SkillMatcher\\scraper"));
            
            // Start the process
            Process process = processBuilder.start();
            
            // Read the output
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            StringBuilder output = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append("\n");
                logger.info("Scraper output: {}", line);
            }
            
            // Read error output
            BufferedReader errorReader = new BufferedReader(new InputStreamReader(process.getErrorStream()));
            StringBuilder errorOutput = new StringBuilder();
            while ((line = errorReader.readLine()) != null) {
                errorOutput.append(line).append("\n");
                logger.error("Scraper error: {}", line);
            }
            
            // Wait for the process to complete
            int exitCode = process.waitFor();
            logger.info("Scraper process exited with code: {}", exitCode);
            
            if (exitCode == 0) {
                // Read the JSON file
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
            @RequestParam String location) {
        try {
            logger.info("Fetching jobs from JobTech API for keyword: {} and location: {}", keyword, location);
            List<JobTechJob> jobs = jobTechService.searchJobs(keyword, location);
            return ResponseEntity.ok(jobs);
        } catch (Exception e) {
            logger.error("Error fetching jobs from JobTech API", e);
            return ResponseEntity.internalServerError().body("Error: " + e.getMessage());
        }
    }
} 