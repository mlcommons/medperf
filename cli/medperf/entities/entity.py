from typing import List, Dict
from abc import ABC, abstractmethod

from medperf.ui.interface import UI
from medperf.comms.interface import Comms

class Entity:
	@abstractmethod
	def all(cls) -> List["Entity"]:
		"""Gets a list of all instances of the respective entity. 
		Wether the list is local or remote depends on the implementation.

		Returns:
			List[Entity]: a list of entities.
		"""

	@abstractmethod
	def get(cls, uid: str) -> "Entity":
		"""Gets an instance of the respective entity.
		Wether this requires only local read or remote calls depends 
		on the implementation.

		Args:
			uid (str): Unique Identifier to retrieve the entity

		Returns:
			Entity: Entity Instance associated to the UID
		"""

	@abstractmethod
	def todict(self) -> Dict:
		"""Dictionary representation of the entity

		Returns:
			Dict: Dictionary containing information about the entity
		"""

	@abstractmethod
	def upload(self, comms: Comms):
		"""Upload the entity-related information to the communication's interface
		"""