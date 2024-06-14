from typing import Union, Optional
from pydantic import BaseModel


class EditCubeData(BaseModel):
    """represents a partial mlcube with fields to be updated"""
    uid: Union[str, int]
    name: Optional[str]
    git_mlcube_url: Optional[str]
    git_mlcube_hash: Optional[str]
    git_parameters_url: Optional[str]
    parameters_hash: Optional[str]
    image_tarball_url: Optional[str]
    image_tarball_hash: Optional[str]
    additional_files_tarball_url: Optional[str]
    additional_files_tarball_hash: Optional[str]

    def not_null_dict(self):
        """returns a dictionary of the non-null fields"""
        return {k: v for k, v in self.dict().items() if v is not None}
