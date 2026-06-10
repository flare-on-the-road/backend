class UserRole:
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class AuthProvider:
    LOCAL = "local"
    GOOGLE = "google"
    NAVER = "naver"
    KAKAO = "kakao"


class FilePurpose:
    PROFILE_IMAGE = "profile_image"
    BOARD_ATTACHMENT = "board_attachment"


class FileStatus:
    ACTIVE = "active"
    DELETED = "deleted"


class PostBoardType:
    BUG = "bug"
    NOTICE = "notice"
    INQUIRY = "inquiry"

    ALL = (BUG, NOTICE, INQUIRY)
