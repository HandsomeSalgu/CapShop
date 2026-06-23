package com.syncshopper.service;

import com.syncshopper.dto.response.AiVerificationResponse;
import com.syncshopper.dto.search.AiVerificationRequest;
import com.syncshopper.dto.search.ScoredSearchCandidate;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class AiCandidateVerificationService {

    public AiVerificationResponse verify(AiVerificationRequest request) {
        List<ScoredSearchCandidate> candidates = request == null ? List.of() : request.getCandidates();
        if (candidates == null || candidates.isEmpty()) {
            return AiVerificationResponse.builder()
                    .bestCandidateIndex(null)
                    .matchLevel("NOT_MATCH")
                    .confidence(0.0)
                    .identifiedName("")
                    .reason("No search candidates were available for verification.")
                    .evidence(List.of())
                    .alternatives(List.of())
                    .build();
        }

        ScoredSearchCandidate best = candidates.getFirst();
        String matchLevel = matchLevel(best.getFinalScore());

        return AiVerificationResponse.builder()
                .bestCandidateIndex(best.getIndex())
                .matchLevel(matchLevel)
                .confidence(confidence(best.getFinalScore()))
                .identifiedName(best.getResult().getTitle())
                .reason(best.getReason())
                .evidence(List.of(
                        "source=" + best.getResult().getSource().name(),
                        "queryText=" + best.getResult().getQueryText(),
                        "score=" + best.getFinalScore()
                ))
                .alternatives(candidates.stream()
                        .skip(1)
                        .limit(3)
                        .map(candidate -> AiVerificationResponse.Alternative.builder()
                                .candidateIndex(candidate.getIndex())
                                .matchLevel(matchLevel(candidate.getFinalScore()))
                                .reason(candidate.getReason())
                                .build())
                        .toList())
                .build();
    }

    public String matchLevel(Double score) {
        double value = score == null ? 0 : score;
        if (value >= 80) {
            return "EXACT";
        }
        if (value >= 55) {
            return "SIMILAR";
        }
        if (value >= 25) {
            return "RELATED";
        }
        return "NOT_MATCH";
    }

    private double confidence(Double score) {
        double value = score == null ? 0 : score;
        return Math.round(Math.max(0.0, Math.min(0.98, value / 100.0)) * 100.0) / 100.0;
    }
}
