# Interfaces Analysis & Refactoring Plan

## Current State

### Application Layer Interfaces (`application/interfaces/`)
**Status**: ⚠️ LEGACY - Used by legacy code only

1. `ILLMRepository` - Legacy LLM interface (used by `rag_use_case.py`, `litellm_client.py`)
2. `IEmbeddingRepository` - Legacy embedding interface (used by legacy embedding services)
3. `IVectorStoreRepository` - Legacy vector store interface (used by `milvus_repository.py`)
4. `IHealthRepository` - Health check interface
5. `ISystemLogRepository` - System log interface
6. `ICacheRepository` - Cache repository interface

### Domain Layer Interfaces (`domain/interfaces/`)
**Status**: ✅ NEW - Used by new 4-layer caching pipeline

1. `ILLMService` - New LLM service interface
2. `IEmbeddingService` - New embedding service interface (Cache #2)
3. `IRetriever` - New retriever interface
4. `ITextCache` - Cache #1 interface
5. `IVectorCache` - Cache #3 interface
6. `ISemanticCache` - Cache #4 interface

---

## Problem Analysis

### Issue 1: Duplicate Concepts
- `ILLMRepository` (application) vs `ILLMService` (domain) - Both for LLM operations
- `IEmbeddingRepository` (application) vs `IEmbeddingService` (domain) - Both for embeddings
- `IVectorStoreRepository` (application) vs `IRetriever` (domain) - Both for retrieval

### Issue 2: Clean Architecture Violation
- Application layer should NOT define interfaces for infrastructure concerns
- Interfaces should be in Domain layer (business logic) or Infrastructure layer (adapters)
- Application layer should only depend on Domain interfaces

### Issue 3: Usage Pattern
- **Legacy code** uses `application/interfaces/*`
- **New pipeline** uses `domain/interfaces/*`
- Both coexist but create confusion

---

## Refactoring Strategy

### Option 1: Migrate to Domain Interfaces (Recommended)
**Pros**:
- Clean Architecture compliant
- Single source of truth
- No duplication

**Cons**:
- Requires refactoring legacy code
- Breaking changes for legacy code

### Option 2: Keep Both (Current State)
**Pros**:
- No breaking changes
- Backward compatibility
- Legacy code continues working

**Cons**:
- Duplication
- Confusion
- Not ideal Clean Architecture

### Option 3: Move Application Interfaces to Domain (Hybrid)
**Pros**:
- Consolidates interfaces
- Better organization
- Clean Architecture compliant

**Cons**:
- Requires careful migration
- Need to update imports

---

## Recommended Solution: Document & Isolate

Since we must preserve all functionality and avoid breaking changes:

1. **Keep Application Interfaces** - For legacy code backward compatibility
2. **Document Clearly** - Mark as legacy, explain usage
3. **Isolate Usage** - Ensure new pipeline only uses domain interfaces
4. **Future Migration** - Plan migration path for legacy code

---

## Action Items

1. ✅ Document application interfaces as legacy
2. ✅ Verify new pipeline uses only domain interfaces
3. ✅ Create migration guide for future refactoring
4. ✅ Add deprecation warnings (optional)

