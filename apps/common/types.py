from pydantic import BaseModel


# https://firebase.google.com/docs/reference/admin/node/firebase-admin.auth.decodedidtoken
class FirebaseDecodedIdToken(BaseModel):
    uid: str
    email_verified: bool
    email: str

    class Config:
        frozen = True

    @property
    def email_lower(self):
        return self.email.lower()
