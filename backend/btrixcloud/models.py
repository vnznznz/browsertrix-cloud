"""
Crawl-related models and types
"""

from datetime import datetime
from enum import Enum, IntEnum
import os

from typing import Optional, List, Dict, Union, Literal, Any
from pydantic import BaseModel, UUID4, conint, Field, HttpUrl, AnyHttpUrl, EmailStr
from fastapi_users import models as fastapi_users_models

from .db import BaseMongoModel

# crawl scale for constraint
MAX_CRAWL_SCALE = int(os.environ.get("MAX_CRAWL_SCALE", 3))


# pylint: disable=invalid-name
# ============================================================================

### MAIN USER MODEL ###


# ============================================================================
class User(fastapi_users_models.BaseUser):
    """
    Base User Model
    """

    name: Optional[str] = ""


# ============================================================================

### CRAWL CONFIGS ###


# ============================================================================
class JobType(str, Enum):
    """Job Types"""

    URL_LIST = "url-list"
    SEED_CRAWL = "seed-crawl"
    CUSTOM = "custom"


# ============================================================================
class ScopeType(str, Enum):
    """Crawl scope type"""

    PAGE = "page"
    PAGE_SPA = "page-spa"
    PREFIX = "prefix"
    HOST = "host"
    DOMAIN = "domain"
    ANY = "any"
    CUSTOM = "custom"


# ============================================================================
class Seed(BaseModel):
    """Crawl seed"""

    url: HttpUrl
    scopeType: Optional[ScopeType]

    include: Union[str, List[str], None]
    exclude: Union[str, List[str], None]
    sitemap: Union[bool, HttpUrl, None]
    allowHash: Optional[bool]
    depth: Optional[int]
    extraHops: Optional[int]


# ============================================================================
class RawCrawlConfig(BaseModel):
    """Base Crawl Config"""

    seeds: List[Seed]

    scopeType: Optional[ScopeType] = ScopeType.PREFIX

    include: Union[str, List[str], None] = None
    exclude: Union[str, List[str], None] = None

    depth: Optional[int] = -1
    limit: Optional[int] = 0
    extraHops: Optional[int] = 0

    lang: Optional[str]
    blockAds: Optional[bool] = False

    behaviorTimeout: Optional[int]
    pageLoadTimeout: Optional[int]
    pageExtraDelay: Optional[int] = 0

    workers: Optional[int]

    headless: Optional[bool]

    generateWACZ: Optional[bool]
    combineWARC: Optional[bool]

    useSitemap: Optional[bool] = False

    logging: Optional[str]
    behaviors: Optional[str] = "autoscroll,autoplay,autofetch,siteSpecific"


# ============================================================================
class CrawlConfigIn(BaseModel):
    """CrawlConfig input model, submitted via API"""

    schedule: Optional[str] = ""
    runNow: Optional[bool] = False

    config: RawCrawlConfig

    name: str

    description: Optional[str]

    jobType: Optional[JobType] = JobType.CUSTOM

    profileid: Optional[str]

    autoAddCollections: Optional[List[UUID4]] = []
    tags: Optional[List[str]] = []

    crawlTimeout: int = 0
    maxCrawlSize: int = 0
    scale: Optional[conint(ge=1, le=MAX_CRAWL_SCALE)] = 1  # type: ignore

    crawlFilenameTemplate: Optional[str]


# ============================================================================
class ConfigRevision(BaseMongoModel):
    """Crawl Config Revision"""

    cid: UUID4

    schedule: Optional[str] = ""

    config: RawCrawlConfig

    profileid: Optional[UUID4]

    crawlTimeout: Optional[int] = 0
    maxCrawlSize: Optional[int] = 0
    scale: Optional[conint(ge=1, le=MAX_CRAWL_SCALE)] = 1  # type: ignore

    modified: datetime
    modifiedBy: Optional[UUID4]

    rev: int = 0


# ============================================================================
class CrawlConfigCore(BaseMongoModel):
    """Core data shared between crawls and crawlconfigs"""

    schedule: Optional[str] = ""

    jobType: Optional[JobType] = JobType.CUSTOM
    config: RawCrawlConfig

    tags: Optional[List[str]] = []

    crawlTimeout: Optional[int] = 0
    maxCrawlSize: Optional[int] = 0
    scale: Optional[conint(ge=1, le=MAX_CRAWL_SCALE)] = 1  # type: ignore

    oid: UUID4

    profileid: Optional[UUID4]


# ============================================================================
class CrawlConfig(CrawlConfigCore):
    """Schedulable config"""

    id: UUID4

    name: Optional[str]
    description: Optional[str]

    created: datetime
    createdBy: Optional[UUID4]

    modified: Optional[datetime]
    modifiedBy: Optional[UUID4]

    autoAddCollections: Optional[List[UUID4]] = []

    inactive: Optional[bool] = False

    rev: int = 0

    crawlAttemptCount: Optional[int] = 0
    crawlCount: Optional[int] = 0
    crawlSuccessfulCount: Optional[int] = 0

    totalSize: Optional[int] = 0

    lastCrawlId: Optional[str]
    lastCrawlStartTime: Optional[datetime]
    lastStartedBy: Optional[UUID4]
    lastCrawlTime: Optional[datetime]
    lastCrawlState: Optional[str]
    lastCrawlSize: Optional[int]

    lastRun: Optional[datetime]

    isCrawlRunning: Optional[bool] = False

    def get_raw_config(self):
        """serialize config for browsertrix-crawler"""
        return self.config.dict(exclude_unset=True, exclude_none=True)


# ============================================================================
class CrawlConfigOut(CrawlConfig):
    """Crawl Config Output"""

    lastCrawlStopping: Optional[bool] = False

    profileName: Optional[str]

    createdByName: Optional[str]
    modifiedByName: Optional[str]
    lastStartedByName: Optional[str]

    firstSeed: Optional[str]


# ============================================================================
class CrawlConfigIdNameOut(BaseMongoModel):
    """Crawl Config id and name output only"""

    name: str


# ============================================================================
class UpdateCrawlConfig(BaseModel):
    """Update crawl config name, crawl schedule, or tags"""

    # metadata: not revision tracked
    name: Optional[str] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    autoAddCollections: Optional[List[UUID4]] = None

    # crawl data: revision tracked
    schedule: Optional[str] = None
    profileid: Optional[str] = None
    crawlTimeout: Optional[int] = None
    maxCrawlSize: Optional[int] = None
    scale: Optional[conint(ge=1, le=MAX_CRAWL_SCALE)] = None  # type: ignore
    crawlFilenameTemplate: Optional[str] = None
    config: Optional[RawCrawlConfig] = None


# ============================================================================

### BASE CRAWLS ###


# ============================================================================
class CrawlFile(BaseModel):
    """file from a crawl"""

    filename: str
    hash: str
    size: int
    def_storage_name: Optional[str]

    presignedUrl: Optional[str]
    expireAt: Optional[datetime]


# ============================================================================
class CrawlFileOut(BaseModel):
    """output for file from a crawl (conformance to Data Resource Spec)"""

    name: str
    path: str
    hash: str
    size: int
    crawlId: Optional[str]


# ============================================================================
class BaseCrawl(BaseMongoModel):
    """Base Crawl object (representing crawls, uploads and manual sessions)"""

    id: str

    userid: UUID4
    oid: UUID4

    started: datetime
    finished: Optional[datetime] = None

    name: Optional[str] = ""

    state: str

    stats: Optional[Dict[str, int]] = None

    files: Optional[List[CrawlFile]] = []

    description: Optional[str] = ""

    errors: Optional[List[str]] = []

    collectionIds: Optional[List[UUID4]] = []

    fileSize: int = 0
    fileCount: int = 0


# ============================================================================
class CollIdName(BaseModel):
    """Collection id and name object"""

    id: UUID4
    name: str


# ============================================================================
class CrawlOut(BaseMongoModel):
    """Crawl output model, shared across all crawl types"""

    # pylint: disable=duplicate-code

    type: Optional[str]

    id: str

    userid: UUID4
    oid: UUID4

    userName: Optional[str]

    name: Optional[str]
    description: Optional[str]

    started: datetime
    finished: Optional[datetime]

    state: str

    stats: Optional[Dict[str, int]]

    fileSize: int = 0
    fileCount: int = 0

    tags: Optional[List[str]] = []

    errors: Optional[List[str]]

    collectionIds: Optional[List[UUID4]] = []

    # automated crawl fields
    config: Optional[RawCrawlConfig]
    cid: Optional[UUID4]
    firstSeed: Optional[str]
    seedCount: Optional[int]
    profileName: Optional[str]
    stopping: Optional[bool]
    manual: Optional[bool]
    cid_rev: Optional[int]

    storageQuotaReached: Optional[bool]


# ============================================================================
class CrawlOutWithResources(CrawlOut):
    """Crawl output model including resources"""

    resources: Optional[List[CrawlFileOut]] = []
    collections: Optional[List[CollIdName]] = []


# ============================================================================
class UpdateCrawl(BaseModel):
    """Update crawl"""

    name: Optional[str]
    description: Optional[str]
    tags: Optional[List[str]]
    collectionIds: Optional[List[UUID4]]


# ============================================================================
class DeleteCrawlList(BaseModel):
    """delete crawl list POST body"""

    crawl_ids: List[str]


# ============================================================================

### AUTOMATED CRAWLS ###


# ============================================================================
class CrawlScale(BaseModel):
    """scale the crawl to N parallel containers"""

    scale: conint(ge=1, le=MAX_CRAWL_SCALE) = 1  # type: ignore


# ============================================================================
class Crawl(BaseCrawl, CrawlConfigCore):
    """Store State of a Crawl (Finished or Running)"""

    type: str = Field("crawl", const=True)

    cid: UUID4

    cid_rev: int = 0

    # schedule: Optional[str]
    manual: Optional[bool]

    stopping: Optional[bool] = False


# ============================================================================
class CrawlCompleteIn(BaseModel):
    """Completed Crawl Webhook POST message"""

    id: str

    user: str

    filename: str
    size: int
    hash: str

    completed: Optional[bool] = True


# ============================================================================

### UPLOADED CRAWLS ###


# ============================================================================
class UploadedCrawl(BaseCrawl):
    """Store State of a Crawl Upload"""

    type: str = Field("upload", const=True)

    tags: Optional[List[str]] = []


# ============================================================================
class UpdateUpload(UpdateCrawl):
    """Update modal that also includes name"""


# ============================================================================

### COLLECTIONS ###


# ============================================================================
class Collection(BaseMongoModel):
    """Org collection structure"""

    name: str = Field(..., min_length=1)
    oid: UUID4
    description: Optional[str]
    modified: Optional[datetime]

    crawlCount: Optional[int] = 0
    pageCount: Optional[int] = 0
    totalSize: Optional[int] = 0

    # Sorted by count, descending
    tags: Optional[List[str]] = []

    isPublic: Optional[bool] = False


# ============================================================================
class CollIn(BaseModel):
    """Collection Passed in By User"""

    name: str = Field(..., min_length=1)
    description: Optional[str]
    crawlIds: Optional[List[str]] = []

    isPublic: Optional[bool] = False


# ============================================================================
class CollOut(Collection):
    """Collection output model with annotations."""

    resources: Optional[List[CrawlFileOut]] = []


# ============================================================================
class UpdateColl(BaseModel):
    """Update collection"""

    name: Optional[str]
    description: Optional[str]
    isPublic: Optional[bool]


# ============================================================================
class AddRemoveCrawlList(BaseModel):
    """Collections to add or remove from collection"""

    crawlIds: Optional[List[str]] = []


# ============================================================================

### INVITES ###


# ============================================================================
class UserRole(IntEnum):
    """User role"""

    VIEWER = 10
    CRAWLER = 20
    OWNER = 40
    SUPERADMIN = 100


# ============================================================================
class InvitePending(BaseMongoModel):
    """An invite for a new user, with an email and invite token as id"""

    created: datetime
    inviterEmail: str
    oid: Optional[UUID4]
    role: Optional[UserRole] = UserRole.VIEWER
    email: Optional[str]


# ============================================================================
class InviteRequest(BaseModel):
    """Request to invite another user"""

    email: str


# ============================================================================
class InviteToOrgRequest(InviteRequest):
    """Request to invite another user to an organization"""

    role: UserRole


# ============================================================================
class AddToOrgRequest(InviteRequest):
    """Request to add a new user to an organization directly"""

    role: UserRole
    password: str
    name: str


# ============================================================================

### ORGS ###


# ============================================================================
class UpdateRole(InviteToOrgRequest):
    """Update existing role for user"""


# ============================================================================
class RemoveFromOrg(InviteRequest):
    """Remove this user from org"""


# ============================================================================
class RemovePendingInvite(InviteRequest):
    """Delete pending invite to org by email"""


# ============================================================================
class RenameOrg(BaseModel):
    """Request to invite another user"""

    name: str


# ============================================================================
class DefaultStorage(BaseModel):
    """Storage reference"""

    type: Literal["default"] = "default"
    name: str
    path: str = ""


# ============================================================================
class S3Storage(BaseModel):
    """S3 Storage Model"""

    type: Literal["s3"] = "s3"

    endpoint_url: str
    access_key: str
    secret_key: str
    access_endpoint_url: Optional[str]
    region: Optional[str] = ""
    use_access_for_presign: Optional[bool] = True


# ============================================================================
class OrgQuotas(BaseModel):
    """Organization quotas (settable by superadmin)"""

    maxConcurrentCrawls: Optional[int] = 0
    maxPagesPerCrawl: Optional[int] = 0
    storageQuota: Optional[int] = 0


# ============================================================================
class OrgWebhookUrls(BaseModel):
    """Organization webhook URLs"""

    crawlStarted: Optional[AnyHttpUrl] = None
    crawlFinished: Optional[AnyHttpUrl] = None
    uploadFinished: Optional[AnyHttpUrl] = None
    addedToCollection: Optional[AnyHttpUrl] = None
    removedFromCollection: Optional[AnyHttpUrl] = None


# ============================================================================
class Organization(BaseMongoModel):
    """Organization Base Model"""

    id: UUID4

    name: str

    users: Dict[str, UserRole]

    storage: Union[S3Storage, DefaultStorage]

    usage: Dict[str, int] = {}

    bytesStored: int = 0

    default: bool = False

    quotas: Optional[OrgQuotas] = OrgQuotas()

    webhookUrls: Optional[OrgWebhookUrls] = OrgWebhookUrls()

    origin: Optional[AnyHttpUrl] = None

    def is_owner(self, user):
        """Check if user is owner"""
        return self._is_auth(user, UserRole.OWNER)

    def is_crawler(self, user):
        """Check if user can crawl (write)"""
        return self._is_auth(user, UserRole.CRAWLER)

    def is_viewer(self, user):
        """Check if user can view (read)"""
        return self._is_auth(user, UserRole.VIEWER)

    def _is_auth(self, user, value):
        """Check if user has at least specified permission level"""
        if user.is_superuser:
            return True

        res = self.users.get(str(user.id))
        if not res:
            return False

        return res >= value

    async def serialize_for_user(self, user: User, user_manager):
        """Serialize result based on current user access"""

        exclude = {"storage"}

        if not self.is_owner(user):
            exclude.add("users")

        if not self.is_crawler(user):
            exclude.add("usage")

        result = self.to_dict(
            exclude_unset=True,
            exclude_none=True,
            exclude=exclude,
        )

        if self.is_owner(user):
            keys = list(result["users"].keys())
            user_list = await user_manager.get_user_names_by_ids(keys)

            for org_user in user_list:
                id_ = str(org_user["id"])
                role = result["users"].get(id_)
                if not role:
                    continue

                result["users"][id_] = {
                    "role": role,
                    "name": org_user.get("name", ""),
                    "email": org_user.get("email", ""),
                }

        return OrgOut.from_dict(result)


# ============================================================================
class OrgOut(BaseMongoModel):
    """Organization API output model"""

    id: UUID4
    name: str
    users: Optional[Dict[str, Any]]
    usage: Optional[Dict[str, int]]
    default: bool = False
    bytesStored: int
    origin: Optional[AnyHttpUrl]

    webhookUrls: Optional[OrgWebhookUrls] = OrgWebhookUrls()
    quotas: Optional[OrgQuotas] = OrgQuotas()


# ============================================================================

### PAGINATION ###


# ============================================================================
class PaginatedResponse(BaseModel):
    """Paginated response model"""

    items: List[Any]
    total: int
    page: int
    pageSize: int


# ============================================================================

### PROFILES ###


# ============================================================================
class ProfileFile(BaseModel):
    """file from a crawl"""

    filename: str
    hash: str
    size: int
    def_storage_name: Optional[str] = ""


# ============================================================================
class Profile(BaseMongoModel):
    """Browser profile"""

    name: str
    description: Optional[str] = ""

    userid: UUID4
    oid: UUID4

    origins: List[str]
    resource: Optional[ProfileFile]

    created: Optional[datetime]
    baseid: Optional[UUID4] = None


# ============================================================================
class ProfileWithCrawlConfigs(Profile):
    """Profile with list of crawlconfigs using this profile"""

    crawlconfigs: List[CrawlConfigIdNameOut] = []


# ============================================================================
class UrlIn(BaseModel):
    """Request to set url"""

    url: HttpUrl


# ============================================================================
class ProfileLaunchBrowserIn(UrlIn):
    """Request to launch new browser for creating profile"""

    profileId: Optional[UUID4]


# ============================================================================
class BrowserId(BaseModel):
    """Profile id on newly created profile"""

    browserid: str


# ============================================================================
class ProfileCreate(BaseModel):
    """Create new profile for browser id"""

    browserid: str
    name: str
    description: Optional[str] = ""


# ============================================================================
class ProfileUpdate(BaseModel):
    """Update existing profile with new browser profile or metadata only"""

    browserid: Optional[str] = ""
    name: str
    description: Optional[str] = ""


# ============================================================================

### USERS ###


# ============================================================================
# use custom model as model.BaseUserCreate includes is_* field
class UserCreateIn(fastapi_users_models.CreateUpdateDictModel):
    """
    User Creation Model exposed to API
    """

    email: EmailStr
    password: str

    name: Optional[str] = ""

    inviteToken: Optional[UUID4]

    newOrg: bool
    newOrgName: Optional[str] = ""


# ============================================================================
class UserCreate(fastapi_users_models.BaseUserCreate):
    """
    User Creation Model
    """

    name: Optional[str] = ""

    inviteToken: Optional[UUID4] = None

    newOrg: bool
    newOrgName: Optional[str] = ""


# ============================================================================
class UserUpdate(User, fastapi_users_models.CreateUpdateDictModel):
    """
    User Update Model
    """

    password: Optional[str]
    email: EmailStr


# ============================================================================
class UserDB(User, fastapi_users_models.BaseUserDB):
    """
    User in DB Model
    """

    invites: Dict[str, InvitePending] = {}


# ============================================================================

### WEBHOOKS ###


# ============================================================================
class WebhookNotificationBody(BaseModel):
    """Base POST body model for webhook notifications"""

    downloadUrls: Optional[List] = None

    # Store as str, not UUID, to make JSON-serializable
    orgId: str


# ============================================================================
class WebhookEventType(str, Enum):
    """Webhook Event Types"""

    CRAWL_STARTED = "crawlStarted"
    CRAWL_FINISHED = "crawlFinished"
    UPLOAD_FINISHED = "uploadFinished"

    ADDED_TO_COLLECTION = "addedToCollection"
    REMOVED_FROM_COLLECTION = "removedFromCollection"


# ============================================================================
class BaseCollectionItemBody(WebhookNotificationBody):
    """Webhook notification base POST body for collection changes"""

    collectionId: str
    itemIds: List[str]


# ============================================================================
class CollectionItemAddedBody(BaseCollectionItemBody):
    """Webhook notification POST body for collection additions"""

    event: str = Field(WebhookEventType.ADDED_TO_COLLECTION, const=True)


# ============================================================================
class CollectionItemRemovedBody(BaseCollectionItemBody):
    """Webhook notification POST body for collection removals"""

    event: str = Field(WebhookEventType.REMOVED_FROM_COLLECTION, const=True)


# ============================================================================
class BaseArchivedItemBody(WebhookNotificationBody):
    """Webhook notification POST body for when archived item is started or finished"""

    itemId: str


# ============================================================================
class CrawlStartedBody(BaseArchivedItemBody):
    """Webhook notification POST body for when crawl starts"""

    scheduled: bool = False
    event: str = Field(WebhookEventType.CRAWL_STARTED, const=True)


# ============================================================================
class CrawlFinishedBody(BaseArchivedItemBody):
    """Webhook notification POST body for when crawl finishes"""

    event: str = Field(WebhookEventType.CRAWL_FINISHED, const=True)
    state: str


# ============================================================================
class UploadFinishedBody(BaseArchivedItemBody):
    """Webhook notification POST body for when upload finishes"""

    event: str = Field(WebhookEventType.UPLOAD_FINISHED, const=True)
    state: str


# ============================================================================
class WebhookNotification(BaseMongoModel):
    """Base POST body model for webhook notifications"""

    event: WebhookEventType
    oid: UUID4
    body: Union[
        CrawlStartedBody,
        CrawlFinishedBody,
        UploadFinishedBody,
        CollectionItemAddedBody,
        CollectionItemRemovedBody,
    ]
    success: bool = False
    attempts: int = 0
    created: datetime
    lastAttempted: Optional[datetime] = None
