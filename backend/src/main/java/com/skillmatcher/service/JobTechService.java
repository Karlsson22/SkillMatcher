package com.skillmatcher.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.skillmatcher.model.JobTechJob;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.ResponseEntity;
import java.io.File;
import java.util.List;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Service
public class JobTechService {
    private static final Logger logger = LoggerFactory.getLogger(JobTechService.class);
    private static final String JOBTECH_API_URL = "https://jobsearch.api.jobtechdev.se/search";
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    public JobTechService() {
        this.restTemplate = new RestTemplate();
        this.objectMapper = new ObjectMapper();
    }

    public List<JobTechJob> searchJobs(String keyword, String location) {
        try {
            // Build the API URL with query parameters
            String url = String.format("%s?q=%s&limit=10&offset=0", 
                JOBTECH_API_URL, 
                keyword.replace(" ", "+"));

            logger.info("Fetching jobs from JobTech API: {}", url);

            // Make the API call
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);
            
            // Log the raw response for debugging
            logger.info("Raw API Response: {}", response.getBody());
            
            // Parse the response
            List<JobTechJob> jobs = new ArrayList<>();
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                JsonNode rootNode = objectMapper.readTree(response.getBody());
                logger.info("Parsed root node: {}", rootNode.toString());
                
                JsonNode hitsNode = rootNode.get("hits");
                logger.info("Hits node: {}", hitsNode != null ? hitsNode.toString() : "null");
                
                if (hitsNode != null && hitsNode.isArray()) {
                    for (JsonNode hit : hitsNode) {
                        try {
                            JobTechJob job = new JobTechJob();
                            
                            // Map the fields from the API response to our JobTechJob object
                            if (hit.has("id")) job.setId(hit.get("id").asText());
                            if (hit.has("headline")) job.setHeadline(hit.get("headline").asText());
                            
                            // Get description from the description.text field
                            JsonNode descriptionNode = hit.get("description");
                            if (descriptionNode != null && descriptionNode.has("text")) {
                                job.setDescription(descriptionNode.get("text").asText());
                            }
                            
                            // Handle employer information
                            JsonNode employerNode = hit.get("employer");
                            if (employerNode != null && employerNode.has("name")) {
                                job.setEmployer(employerNode.get("name").asText());
                            }
                            
                            // Handle location information
                            JsonNode workplaceNode = hit.get("workplace");
                            if (workplaceNode != null && workplaceNode.has("municipality")) {
                                job.setLocation(workplaceNode.get("municipality").asText());
                            }
                            
                            // Set the URL
                            if (job.getId() != null) {
                                job.setUrl("https://jobsearch.api.jobtechdev.se/ad/" + job.getId());
                            }
                            
                            // Handle dates
                            if (hit.has("publication_date")) {
                                job.setPublicationDate(hit.get("publication_date").asText());
                            }
                            if (hit.has("application_deadline")) {
                                job.setApplicationDeadline(hit.get("application_deadline").asText());
                            }
                            
                            jobs.add(job);
                            logger.info("Added job: {}", job.getHeadline());
                        } catch (Exception e) {
                            logger.error("Error processing job: {}", e.getMessage());
                        }
                    }
                } else {
                    logger.warn("No hits found in the response or hits is not an array");
                }
            } else {
                logger.warn("API call was not successful. Status code: {}", response.getStatusCode());
            }

            // Save to JSON file
            saveToJsonFile(jobs);

            return jobs;
        } catch (Exception e) {
            logger.error("Error fetching jobs from JobTech API: {}", e.getMessage(), e);
            throw new RuntimeException("Failed to fetch jobs from JobTech API", e);
        }
    }

    private void saveToJsonFile(List<JobTechJob> newJobs) {
        try {
            // Use absolute path to the scraper directory
            String scraperDir = "C:\\Users\\defau\\Cursor_Projekts\\SkillMatcher\\scraper";
            File outputFile = new File(scraperDir, "jobs.json");
            
            // Read existing jobs if file exists
            List<JobTechJob> allJobs = new ArrayList<>();
            if (outputFile.exists()) {
                try {
                    allJobs = objectMapper.readValue(outputFile, 
                        objectMapper.getTypeFactory().constructCollectionType(List.class, JobTechJob.class));
                    logger.info("Read {} existing jobs from file", allJobs.size());
                } catch (Exception e) {
                    logger.warn("Error reading existing jobs file: {}", e.getMessage());
                }
            }
            
            // Add new jobs
            allJobs.addAll(newJobs);
            
            // Save all jobs back to file
            objectMapper.writeValue(outputFile, allJobs);
            logger.info("Saved total of {} jobs to {}", allJobs.size(), outputFile.getAbsolutePath());
        } catch (Exception e) {
            logger.error("Error saving jobs to JSON file: {}", e.getMessage(), e);
            throw new RuntimeException("Failed to save jobs to JSON file", e);
        }
    }
} 