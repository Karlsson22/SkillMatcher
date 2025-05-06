package com.skillmatcher.repository;

import com.skillmatcher.model.Job;
import com.skillmatcher.model.ExperienceLevel;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface JobRepository extends JpaRepository<Job, Long> {
    List<Job> findByExperienceLevel(ExperienceLevel experienceLevel);
} 