# Implementation Plan: Krishi Production-Ready System

## Overview

This implementation plan combines AWS Bedrock AI integration with reliability hardening to create a production-ready MVP system for 100-500 farmers. The plan is organized into 7 phases:

1. **Foundation Infrastructure**: Retry logic, circuit breakers, caching, validation
2. **AWS Bedrock Integration**: Foundation models, RAG engine, Knowledge Base
3. **Bedrock Agent & Voice Services**: Agent creation, enhanced Transcribe/Polly/Translate
4. **Reliability & Error Handling**: Comprehensive error handling, fallbacks, monitoring
5. **Farmer Onboarding**: AI agent-based conversational onboarding
6. **AWS Deployment**: CloudFront, backend scaling, infrastructure as code
7. **Testing & Optimization**: End-to-end testing, performance tuning, cost optimization

## Tasks

### Phase 1: Foundation Infrastructure (Weeks 1-2)

- [x] 1. Set up backend infrastructure for reliability
  - [x] 1.1 Create retry decorator with exponential backoff
    - Use tenacity library for retry logic
    - Configure: max 3 attempts, exponential backoff (1s, 2s, 4s)
    - Retry on: connection errors, timeouts, 5xx status codes
    - _Requirements: 5.1_
  
  - [x] 1.2 Create circuit breaker for service protection
    - Implement CircuitBreaker class with CLOSED/OPEN/HALF_OPEN states
    - Configure: 5 failures threshold, 60s timeout
    - Create separate instances for each external service
    - _Requirements: 5.7_
  
  - [ ] 1.3 Create cache service with TTL support
    - Implement in-memory cache with timestamps
    - Configure TTLs: prices (6h), weather (3h), news (1h), mappings (24h)
    - Add get/set/invalidate methods
    - Support both in-memory and Redis backends
    - _Requirements: 5.2, 5.3, 9.2, 9.3_
  
  - [ ] 1.4 Set up basic structured logging
    - Configure structlog with JSON formatter
    - Add correlation ID middleware
    - Log API calls with service, endpoint, status, duration
    - _Requirements: 13.1, 13.7_

- [x] 2. Create Pydantic validation models for API responses
  - [x] 2.1 Create CEDAPriceResponse model
    - Validate min_price, max_price are positive
    - Validate max_price >= min_price
    - Include data_source and data_timestamp fields
    - _Requirements: 10.2_
  
  - [x] 2.2 Create WeatherResponse model
    - Validate forecast_date is in future
    - Validate precipitation_probability in [0, 100]
    - Include data_source and data_timestamp fields
    - _Requirements: 10.3_
  
  - [x] 2.3 Create DecisionScenario model
    - Validate all required fields present
    - Validate expected_revenue_range is tuple of positive floats
    - _Requirements: 10.1_

- [x] 3. Integrate and harden existing services
  - [x] 3.1 Add retry and circuit breaker to Weather API calls
    - Apply retry decorator to all weather API calls
    - Wrap with circuit breaker instance
    - _Requirements: 5.1, 5.4_
  
  - [x] 3.2 Add retry and circuit breaker to CEDA API calls
    - Apply retry decorator to get_market_prices and initialization
    - Wrap with circuit breaker instance
    - _Requirements: 5.1, 5.3_
  
  - [x] 3.3 Add retry and circuit breaker to News service
    - Apply retry decorator to news API calls
    - Wrap with circuit breaker instance
    - _Requirements: 5.1_

### Phase 2: AWS Bedrock Integration (Weeks 3-4)

- [ ] 4. Set up AWS Bedrock foundation models
  - [ ] 4.1 Create FoundationModelRouter class
    - Implement query complexity analyzer
    - Route simple queries to Claude 3 Haiku
    - Route complex queries to Claude 3.5 Sonnet
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [ ] 4.2 Implement Claude 3.5 Sonnet integration
    - Configure model ID: anthropic.claude-3-5-sonnet-20241022-v2:0
    - Implement streaming response support
    - Add error handling with fallback
    - _Requirements: 1.1, 1.6, 1.7, 1.8_
  
  - [ ] 4.3 Implement Claude 3 Haiku integration
    - Configure model ID: anthropic.claude-3-haiku-20240307-v1:0
    - Implement streaming response support
    - Add error handling with fallback
    - _Requirements: 1.2, 1.6, 1.7, 1.8_
  
  - [ ] 4.4 Add prompt caching for cost optimization
    - Cache system prompts
    - Cache knowledge base context
    - Track cache hit rate
    - _Requirements: 14.11_

- [ ] 5. Build Knowledge Base and RAG engine
  - [ ] 5.1 Create Amazon Bedrock Knowledge Base
    - Set up OpenSearch Serverless collection
    - Configure Titan Embeddings G1 - Text
    - Define metadata schema (language, crop_type, category)
    - _Requirements: 2.1, 2.5, 2.6, 2.8_
  
  - [ ] 5.2 Ingest agricultural documents
    - Prepare crop advisory documents (English, Telugu, Hindi)
    - Prepare farming best practices documentation
    - Prepare government scheme information
    - Chunk documents into 300-500 tokens with 10% overlap
    - _Requirements: 2.2, 2.3, 2.4, 2.7_
  
  - [ ] 5.3 Implement RAG Engine
    - Create RAGEngine class with retrieve and generate methods
    - Implement semantic search over Knowledge Base
    - Retrieve top 5 relevant documents per query
    - Combine context with query for Foundation Model
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  
  - [ ] 5.4 Add multilingual RAG support
    - Support queries in English, Telugu, Hindi
    - Retrieve language-specific documents when available
    - Translate responses when needed
    - _Requirements: 3.6, 3.7, 3.8_
  
  - [ ] 5.5 Implement source attribution
    - Include source documents in RAG responses
    - Calculate confidence scores
    - Handle cases with no relevant information
    - _Requirements: 3.5, 3.9_

### Phase 3: Bedrock Agent & Enhanced Voice Services (Weeks 5-6)

- [ ] 6. Create Bedrock Agent with action groups
  - [ ] 6.1 Set up Bedrock Agent
    - Create agent with Claude 3.5 Sonnet
    - Configure session management
    - Implement conversation context persistence
    - _Requirements: 4.1, 4.8, 4.9, 4.10_
  
  - [ ] 6.2 Define Weather Action Group
    - Create Lambda function for weather lookup
    - Define OpenAPI schema for action
    - Test agent invocation
    - _Requirements: 4.2, 4.6, 4.7_
  
  - [ ] 6.3 Define Market Price Action Group
    - Create Lambda function for price lookup
    - Define OpenAPI schema for action
    - Test agent invocation
    - _Requirements: 4.3, 4.6, 4.7_
  
  - [ ] 6.4 Define News Action Group
    - Create Lambda function for news retrieval
    - Define OpenAPI schema for action
    - Test agent invocation
    - _Requirements: 4.4, 4.6, 4.7_
  
  - [ ] 6.5 Define Decision Support Action Group
    - Create Lambda function for decision scenarios
    - Define OpenAPI schema for action
    - Test agent invocation
    - _Requirements: 4.5, 4.6, 4.7_
  
  - [ ] 6.6 Implement session summarization
    - Summarize context after 10 turns
    - Manage token limits
    - Preserve critical information
    - _Requirements: 4.11_

- [ ] 7. Enhance voice services with AWS AI
  - [ ] 7.1 Implement Amazon Transcribe integration
    - Support Telugu (te-IN), Hindi (hi-IN), English (en-IN)
    - Handle audio upload to S3
    - Poll for transcription completion
    - Add error handling and fallback
    - _Requirements: 6.1, 6.2_
  
  - [ ] 7.2 Implement Amazon Polly integration
    - Configure neural voices: Kajal (Telugu), Aditi (Hindi), Aria (English)
    - Generate speech from text
    - Return audio stream
    - Add error handling
    - _Requirements: 6.3, 6.4_
  
  - [ ] 7.3 Implement Amazon Translate integration
    - Support cross-language translation
    - Translate responses when needed
    - Cache translations
    - _Requirements: 6.5_
  
  - [ ] 7.4 Implement Amazon Comprehend integration
    - Extract entities from user input
    - Perform sentiment analysis
    - Enhance intent detection
    - _Requirements: 6.6_

- [x] 8. Improve voice interaction reliability
  - [x] 8.1 Implement voice state machine
    - Define states: IDLE, LISTENING, PROCESSING, THINKING, SPEAKING, PAUSED, ERROR
    - Implement state transition validation
    - Add state change callbacks
    - Use refs for immediate state access
    - _Requirements: 6.7, 6.8, 6.9_
  
  - [x] 8.2 Implement barge-in detection
    - Stop audio playback when speech detected during SPEAKING
    - Transition from SPEAKING to PROCESSING
    - Stop within 500ms
    - _Requirements: 6.7_
  
  - [x] 8.3 Enhance echo cancellation
    - Check if transcript is substring of AI response
    - Ignore short inputs during playback
    - Continue listening instead of processing echo
    - _Requirements: 6.8_
  
  - [x] 8.4 Implement automatic listening restart
    - Restart after 5 seconds of silence
    - Restart after audio playback completes
    - _Requirements: 6.9_
  
  - [x] 8.5 Handle microphone permission denial
    - Display clear instructions
    - Offer text input fallback
    - _Requirements: 6.11_

### Phase 4: Reliability & Error Handling (Week 7)

- [ ] 9. Implement comprehensive error handling
  - [ ] 9.1 Add fallback responses for all services
    - CEDA fallback: cached or synthetic data
    - Weather fallback: safe default assessment
    - AI fallback: default "please rephrase" response
    - _Requirements: 5.2, 5.3, 5.4, 5.5_
  
  - [ ] 9.2 Implement data validation
    - Validate all API responses with Pydantic models
    - Log validation errors
    - Return fallback data on validation failure
    - _Requirements: 8.4_
  
  - [ ] 9.3 Add user-friendly error messages
    - Create error message translations (English, Telugu, Hindi)
    - Display errors in user's selected language
    - Provide actionable next steps
    - _Requirements: 8.5_
  
  - [ ] 9.4 Implement input validation
    - Fuzzy matching for invalid crop names
    - Fuzzy matching for invalid locations
    - Suggest corrections to user
    - _Requirements: 8.1, 8.2_
  
  - [ ] 9.5 Add missing field validation
    - Validate required fields in requests
    - Prompt user for missing information
    - Preserve user input on validation failure
    - _Requirements: 8.3, 8.6_
  
  - [ ] 9.6 Implement fallback data transparency
    - Add data_source field to all responses
    - Add data_timestamp field
    - Display cache age to users
    - _Requirements: 8.7_

- [ ] 10. Add monitoring and observability
  - [ ] 10.1 Implement API call logging
    - Log all external API calls
    - Include service, endpoint, status, duration
    - Add correlation IDs
    - _Requirements: 13.1_
  
  - [ ] 10.2 Implement error logging
    - Log errors with full context
    - Include user action, service, timestamp
    - Add stack traces
    - _Requirements: 13.2_
  
  - [ ] 10.3 Implement voice interaction logging
    - Log completed interactions
    - Include transcript, intent, response
    - Track conversation flows
    - _Requirements: 13.3_
  
  - [ ] 10.4 Create health check endpoints
    - Implement /health/live endpoint
    - Implement /health/ready endpoint
    - Check all dependencies (CEDA, Weather, AI, News, Cache)
    - Include latency metrics
    - _Requirements: 13.4_
  
  - [ ] 10.5 Set up CloudWatch metrics
    - Track request count, latency, error rate
    - Track AI token usage and costs
    - Track cache hit rate
    - Track circuit breaker states
    - _Requirements: 13.5, 13.8_
  
  - [ ] 10.6 Configure CloudWatch alarms
    - High error rate (> 5% in 5 minutes)
    - High latency (p95 > 5 seconds)
    - Circuit breaker open
    - High cost (daily > $50)
    - _Requirements: 11.8_

### Phase 5: Farmer Onboarding (Week 8)

- [ ] 11. Implement AI agent-based onboarding
  - [x] 11.1 Create OnboardingService class
    - Initialize with AI service and data services
    - Define system prompts for English, Telugu, Hindi
    - Implement conversation state management
    - _Requirements: 7.1, 7.10_
  
  - [x] 11.2 Implement conversational profile collection
    - Collect name through natural conversation
    - Collect location through natural conversation
    - Collect primary crop through natural conversation
    - Collect farm size through natural conversation
    - _Requirements: 7.2, 7.3, 7.4, 7.5_
  
  - [x] 11.3 Handle multi-turn conversations
    - Acknowledge multiple pieces of information at once
    - Ask follow-up questions only for missing info
    - Maintain conversation context
    - _Requirements: 7.11, 7.12_
  
  - [ ] 11.4 Generate initial decision scenario
    - Fetch weather forecast for farmer's location
    - Fetch market prices for farmer's crop
    - Fetch relevant agricultural news
    - Generate comprehensive recommendation
    - _Requirements: 7.6, 7.7, 7.8, 7.9_
  
  - [ ] 11.5 Create onboarding API endpoints
    - POST /api/onboarding/start - Start new session
    - POST /api/onboarding/process - Process user input
    - GET /api/onboarding/status - Check session status
    - _Requirements: 7.1_
  
  - [ ] 11.6 Add onboarding UI components
    - Create OnboardingFlow component
    - Integrate with voice interaction
    - Display profile collection progress
    - Show decision scenario results
    - _Requirements: 7.1_

### Phase 6: AWS Deployment (Weeks 9-10)

- [ ] 12. Set up AWS infrastructure
  - [ ] 12.1 Create S3 bucket for frontend
    - Configure bucket as private
    - Enable versioning
    - Set up lifecycle policies
    - _Requirements: 12.7_
  
  - [ ] 12.2 Set up CloudFront distribution
    - Configure S3 origin
    - Set up SSL certificate
    - Configure cache behaviors
    - Set up custom domain
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_
  
  - [ ] 12.3 Deploy backend to AWS
    - Choose deployment option (Lambda or ECS)
    - Set up API Gateway
    - Configure auto-scaling
    - Set up health checks
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
  
  - [ ] 12.4 Set up ElastiCache Redis cluster
    - Configure cluster size
    - Set up security groups
    - Configure backup retention
    - _Requirements: 14.6_
  
  - [ ] 12.5 Configure Secrets Manager
    - Store API keys
    - Store database credentials
    - Set up automatic rotation
    - _Requirements: 14.6_
  
  - [ ] 12.6 Set up CloudWatch logging
    - Create log groups
    - Configure retention policies (30 days dev, 90 days prod)
    - Set up log insights queries
    - _Requirements: 13.7, 14.5_

- [ ] 13. Implement infrastructure as code
  - [ ] 13.1 Create AWS CDK project
    - Initialize CDK project
    - Define stack structure
    - Set up environments (dev, staging, prod)
    - _Requirements: 15.1, 15.7_
  
  - [ ] 13.2 Define compute resources
    - Lambda functions or ECS services
    - API Gateway
    - Auto-scaling policies
    - _Requirements: 15.5_
  
  - [ ] 13.3 Define storage resources
    - S3 buckets
    - ElastiCache cluster
    - OpenSearch Serverless
    - _Requirements: 15.5_
  
  - [ ] 13.4 Define networking resources
    - VPC configuration
    - Security groups
    - Load balancers
    - _Requirements: 15.5_
  
  - [ ] 13.5 Define monitoring resources
    - CloudWatch log groups
    - CloudWatch alarms
    - SNS topics for notifications
    - _Requirements: 15.5_
  
  - [ ] 13.6 Add deployment automation
    - Validate infrastructure changes
    - Implement rollback on failure
    - Add deployment scripts
    - _Requirements: 15.2, 15.3, 15.4_
  
  - [ ] 13.7 Tag all resources
    - Add environment tags
    - Add feature tags
    - Enable cost allocation tracking
    - _Requirements: 14.12_

### Phase 7: Testing & Optimization (Weeks 11-12)

- [ ] 14. Implement comprehensive testing
  - [ ] 14.1 Write unit tests for core services
    - Test FoundationModelRouter
    - Test RAGEngine
    - Test OnboardingService
    - Test CircuitBreaker
    - Test CacheService
    - Target: 70% code coverage
    - _Requirements: 10.6_
  
  - [ ] 14.2 Write integration tests
    - Test Bedrock integration
    - Test Knowledge Base queries
    - Test Agent invocations
    - Test voice services
    - _Requirements: 10.5_
  
  - [ ] 14.3 Write property-based tests
    - Test data validation properties
    - Test state machine properties
    - Test cache TTL enforcement
    - Test retry logic
    - _Requirements: 10.7_
  
  - [ ] 14.4 Write end-to-end tests
    - Test complete voice interaction flows
    - Test onboarding flow
    - Test multi-language support
    - Test error recovery
    - _Requirements: 10.5_
  
  - [ ] 14.5 Perform load testing
    - Test with 100 concurrent users
    - Measure response times
    - Identify bottlenecks
    - Verify auto-scaling
    - _Requirements: 11.2, 11.3_

- [ ] 15. Optimize performance and costs
  - [ ] 15.1 Optimize query complexity analyzer
    - Fine-tune classification rules
    - Measure accuracy
    - Adjust thresholds
    - _Requirements: 14.9, 14.10_
  
  - [ ] 15.2 Implement prompt caching
    - Cache system prompts
    - Cache knowledge base context
    - Measure cache hit rate
    - _Requirements: 14.11_
  
  - [ ] 15.3 Optimize caching strategy
    - Tune TTL values
    - Implement cache warming
    - Monitor cache hit rates
    - Target: > 60% hit rate
    - _Requirements: 14.13_
  
  - [ ] 15.4 Optimize CloudFront caching
    - Configure cache behaviors
    - Set appropriate TTLs
    - Implement cache invalidation
    - _Requirements: 14.9_
  
  - [ ] 15.5 Set up cost monitoring
    - Configure billing alarms
    - Set up budget alerts
    - Track costs by service
    - Optimize resource usage
    - _Requirements: 14.7_
  
  - [ ] 15.6 Performance tuning
    - Optimize database queries
    - Reduce API call latency
    - Minimize cold starts
    - Target: p95 < 2 seconds
    - _Requirements: 11.8_

- [ ] 16. Final production readiness
  - [ ] 16.1 Security audit
    - Review IAM policies
    - Check secret rotation
    - Verify HTTPS enforcement
    - Test rate limiting
    - _Requirements: 12.4_
  
  - [ ] 16.2 Documentation
    - API documentation
    - Deployment guide
    - Troubleshooting guide
    - User manual
    - _Requirements: 15.6_
  
  - [ ] 16.3 Disaster recovery plan
    - Backup strategy
    - Recovery procedures
    - Failover testing
    - _Requirements: 11.5, 11.6_
  
  - [ ] 16.4 Production deployment
    - Deploy to production environment
    - Verify all services
    - Monitor for issues
    - _Requirements: 11.6_
  
  - [ ] 16.5 User onboarding
    - Create onboarding materials
    - Train initial users
    - Gather feedback
    - _Requirements: 7.1_

## Notes

- Tasks marked with `[x]` are already completed from previous work
- Each task references specific requirements for traceability
- Phases can overlap for parallel development
- Property-based tests are optional for faster MVP
- Backend uses Python with pytest and hypothesis
- Frontend uses React/TypeScript with vitest
- Infrastructure uses AWS CDK (TypeScript)

## Priority Focus Areas

This task list prioritizes:
1. **Foundation Infrastructure** (Phase 1): Retry, circuit breaker, caching, validation
2. **AWS Bedrock Integration** (Phase 2): Foundation models, RAG, Knowledge Base
3. **Bedrock Agent & Voice** (Phase 3): Agent creation, enhanced voice services
4. **Reliability** (Phase 4): Error handling, monitoring, observability
5. **Farmer Onboarding** (Phase 5): AI agent-based conversational onboarding
6. **AWS Deployment** (Phase 6): CloudFront, backend scaling, infrastructure as code
7. **Testing & Optimization** (Phase 7): Comprehensive testing, performance tuning, cost optimization

## Estimated Timeline

- **Phase 1**: 2 weeks (Foundation Infrastructure)
- **Phase 2**: 2 weeks (AWS Bedrock Integration)
- **Phase 3**: 2 weeks (Bedrock Agent & Voice Services)
- **Phase 4**: 1 week (Reliability & Error Handling)
- **Phase 5**: 1 week (Farmer Onboarding)
- **Phase 6**: 2 weeks (AWS Deployment)
- **Phase 7**: 2 weeks (Testing & Optimization)

**Total**: 12 weeks (3 months) for complete production-ready system
