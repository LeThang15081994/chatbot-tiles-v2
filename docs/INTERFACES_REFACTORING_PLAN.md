# Interfaces Refactoring Plan

## Current State Analysis

### Application Interfaces (`application/interfaces/`)
**Status**: ⚠️ LEGACY - Used by legacy code

| Interface | Used By | Status | Replacement |
|-----------|---------|--------|-------------|
| `ILLMRepository` | `rag_use_case.py` (legacy) | Legacy | `domain/interfaces/llm_service_interface.py` → `ILLMService` |
| `IEmbeddingRepository` | Legacy embedding services | Legacy | `domain/interfaces/embedding_service_interface.py` → `IEmbeddingService` |
| `IVectorStoreRepository` | `search_use_case.py`, `milvus_repository.py` | ⚠️ Active | `domain/interfaces/retriever_interface.py` → `IRetriever` |
| `IHealthRepository` | Health check services | ✅ Active | Keep (no domain equivalent) |
| `ISystemLogRepository` | System logging services | ✅ Active | Keep (no domain equivalent) |
| `ICacheRepository` | Legacy cache implementations | Legacy | Domain cache interfaces |

### Domain Interfaces (`domain/interfaces/`)
**Status**: ✅ NEW - Used by new 4-layer caching pipeline

| Interface | Used By | Status |
|-----------|---------|--------|
| `ILLMService` | `chat_service.py` (new) | ✅ Active |
| `IEmbeddingService` | `answer_cache_facade.py` | ✅ Active |
| `IRetriever` | `answer_cache_facade.py` | ✅ Active |
| `ITextCache` | `answer_cache_facade.py` | ✅ Active |
| `IVectorCache` | `answer_cache_facade.py` | ✅ Active |
| `ISemanticCache` | `answer_cache_facade.py` | ✅ Active |

---

## Issues Identified

### Issue 1: `search_use_case.py` Uses Application Interface
- **File**: `application/use_cases/search_use_case.py`
- **Problem**: Uses `IVectorStoreRepository` from application layer
- **Violation**: Application layer should not define infrastructure interfaces
- **Impact**: Clean Architecture violation

### Issue 2: Duplicate Concepts
- `ILLMRepository` (app) vs `ILLMService` (domain) - Both for LLM
- `IEmbeddingRepository` (app) vs `IEmbeddingService` (domain) - Both for embeddings
- `IVectorStoreRepository` (app) vs `IRetriever` (domain) - Both for retrieval

### Issue 3: Mixed Usage
- Legacy code uses application interfaces
- New code uses domain interfaces
- Both coexist but create confusion

---

## Refactoring Strategy

### Phase 1: Document & Isolate (Current)
✅ **Completed**:
- Created README files for both interface folders
- Documented legacy vs new interfaces
- Isolated usage patterns

### Phase 2: Verify New Code Compliance
✅ **Completed**:
- Verified `chat_service.py` uses domain interfaces only
- Verified `answer_cache_facade.py` uses domain interfaces only
- Verified new infrastructure implementations use domain interfaces

### Phase 3: Legacy Code Isolation (Current)
⚠️ **In Progress**:
- `rag_use_case.py` - Uses `ILLMRepository` (legacy, isolated)
- `search_use_case.py` - Uses `IVectorStoreRepository` (needs review)
- `system_log_use_case.py` - Uses `ISystemLogRepository` (keep, no domain equivalent)

### Phase 4: Future Migration (Optional)
⏳ **Future**:
- Migrate `search_use_case.py` to use `IRetriever` if compatible
- Keep application interfaces for backward compatibility
- Gradually migrate legacy code to domain interfaces

---

## Action Items

### Immediate (Completed)
1. ✅ Created README files documenting interface usage
2. ✅ Verified new code uses domain interfaces only
3. ✅ Documented legacy code isolation

### Short-term (Recommended)
1. ⏳ Review `search_use_case.py` - Can it use `IRetriever`?
2. ⏳ Add deprecation warnings to application interfaces (optional)
3. ⏳ Create migration guide for future refactoring

### Long-term (Optional)
1. ⏳ Migrate `search_use_case.py` to domain interfaces
2. ⏳ Migrate `rag_use_case.py` to domain interfaces
3. ⏳ Consolidate interfaces (if desired)

---

## Clean Architecture Compliance

### Current State
- ✅ **New Pipeline**: Uses domain interfaces only
- ⚠️ **Legacy Code**: Uses application interfaces (isolated)
- ✅ **No Breaking Changes**: Both coexist

### Compliance Status
| Layer | Interfaces | Status |
|-------|-----------|--------|
| Domain | `domain/interfaces/*` | ✅ Compliant |
| Application | `application/interfaces/*` | ⚠️ Legacy (preserved) |
| Infrastructure | Implements domain interfaces | ✅ Compliant |

---

## Recommendations

### For New Code
✅ **ALWAYS** use `domain/interfaces/*`
❌ **NEVER** use `application/interfaces/*` for new code

### For Legacy Code
⚠️ **CONTINUE** using `application/interfaces/*` for backward compatibility
📝 **DOCUMENT** that these are legacy interfaces

### For Infrastructure
✅ **IMPLEMENT** domain interfaces
❌ **DO NOT** implement application interfaces for new code

---

## Summary

| Category | Status | Action |
|----------|--------|--------|
| Domain Interfaces | ✅ Active | Use for new code |
| Application Interfaces | ⚠️ Legacy | Preserve for backward compatibility |
| New Code Compliance | ✅ Verified | Uses domain interfaces only |
| Legacy Code Isolation | ✅ Complete | Documented and isolated |
| Clean Architecture | ✅ Compliant | New pipeline follows CA strictly |

