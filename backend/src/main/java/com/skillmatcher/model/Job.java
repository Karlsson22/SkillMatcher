package com.skillmatcher.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.List;

@Entity
@Table(name = "jobs")
public class Job {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String title;
    
    @Column(columnDefinition = "TEXT")
    private String description;
    
    @Column(nullable = false)
    private String company;
    
    @Column(nullable = false)
    private String location;
    
    @Column(nullable = false)
    private String url;
    
    @Column(nullable = false)
    private String source;
    
    @Column(name = "posted_date")
    private LocalDateTime postedDate;
    
    @Column(name = "scraped_date")
    private LocalDateTime scrapedDate;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "experience_level")
    private ExperienceLevel experienceLevel;
    
    @ElementCollection
    @CollectionTable(name = "job_years_experience", joinColumns = @JoinColumn(name = "job_id"))
    @Column(name = "years")
    private List<Integer> yearsOfExperience;
    
    @Column(name = "max_years_required")
    private Integer maxYearsRequired;

    @Column(name = "deadline")
    private String deadline;

    // Getters and setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public String getCompany() { return company; }
    public void setCompany(String company) { this.company = company; }
    public String getLocation() { return location; }
    public void setLocation(String location) { this.location = location; }
    public String getUrl() { return url; }
    public void setUrl(String url) { this.url = url; }
    public String getSource() { return source; }
    public void setSource(String source) { this.source = source; }
    public LocalDateTime getPostedDate() { return postedDate; }
    public void setPostedDate(LocalDateTime postedDate) { this.postedDate = postedDate; }
    public LocalDateTime getScrapedDate() { return scrapedDate; }
    public void setScrapedDate(LocalDateTime scrapedDate) { this.scrapedDate = scrapedDate; }
    public ExperienceLevel getExperienceLevel() { return experienceLevel; }
    public void setExperienceLevel(ExperienceLevel experienceLevel) { this.experienceLevel = experienceLevel; }
    public List<Integer> getYearsOfExperience() { return yearsOfExperience; }
    public void setYearsOfExperience(List<Integer> yearsOfExperience) { this.yearsOfExperience = yearsOfExperience; }
    public Integer getMaxYearsRequired() { return maxYearsRequired; }
    public void setMaxYearsRequired(Integer maxYearsRequired) { this.maxYearsRequired = maxYearsRequired; }
    public String getDeadline() { return deadline; }
    public void setDeadline(String deadline) { this.deadline = deadline; }
} 