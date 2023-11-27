from medperf.commands.list import EntityList
import medperf.commands.list as list_module
from medperf.exceptions import InvalidArgumentError
import pytest
from medperf.entities.interface import Entity
from medperf.entities.schemas import DeployableEntity


def generate_display_dicts():
    """Mocks a list of dicts to be returned by Entity.display_dict"""
    return [
        {"UID": 1, "Registered": True, "Is Valid": False, "Benchmark": 4},
        {"UID": 2, "Registered": True, "Is Valid": False, "Benchmark": 1},
        {"UID": 3, "Registered": False, "Is Valid": True, "Benchmark": 7},
    ]


@pytest.fixture()
def setup(request, mocker, ui):
    # system inputs
    display_dicts = request.param["display_dicts"]

    # mocks
    entity_object = mocker.create_autospec(spec=Entity)
    # As object has to be Entity + DeployableSchema, it requires `is_valid` field.
    # autospec does not create such a field as in schema is declared as class attribute
    # rather than instance attribute. Thus, for testing purposes we have to create attr manually
    entity_object.is_valid = True
    mocker.patch.object(entity_object, "display_dict", side_effect=display_dicts)
    mocker.patch("medperf.commands.list.get_medperf_user_data", return_value={"id": 1})

    # spies
    generated_entities = [entity_object for _ in display_dicts]
    print([e.is_valid for e in generated_entities])
    all_spy = mocker.patch(
        "medperf.entities.schemas.DeployableEntity.all", return_value=generated_entities
    )
    ui_spy = mocker.patch.object(ui, "print")
    tabulate_spy = mocker.spy(list_module, "tabulate")

    state_variables = {"display_dicts": display_dicts}
    spies = {"ui": ui_spy, "all": all_spy, "tabulate": tabulate_spy}
    return state_variables, spies


@pytest.mark.parametrize(
    "setup", [{"display_dicts": generate_display_dicts()}], indirect=True
)
class TestEntityList:
    @pytest.fixture(autouse=True)
    def set_common_attributes(self, setup):
        state_variables, spies = setup
        self.state_variables = state_variables
        self.spies = spies

    @pytest.mark.parametrize("local_only", [False, True])
    @pytest.mark.parametrize("mine_only", [False, True])
    @pytest.mark.parametrize("valid_only", [False, True])
    def test_entity_all_is_called_properly(self, mocker, local_only, mine_only, valid_only):
        # Arrange
        filters = {"owner": 1} if mine_only else {}

        # Act
        EntityList.run(DeployableEntity, [], local_only, mine_only, valid_only)

        # Assert
        self.spies["all"].assert_called_once_with(
            local_only=local_only, filters=filters
        )

    @pytest.mark.parametrize("fields", [["UID", "MLCube"]])
    def test_exception_raised_for_invalid_input(self, fields):
        # Act & Assert
        with pytest.raises(InvalidArgumentError):
            EntityList.run(DeployableEntity, fields)

    @pytest.mark.parametrize("fields", [["UID", "Is Valid"], ["Registered"]])
    def test_display_calls_tabulate_and_ui_as_expected(self, fields):
        # Arrange
        expected_list = [
            [dict_[field] for field in fields]
            for dict_ in self.state_variables["display_dicts"]
        ]

        # Act
        EntityList.run(DeployableEntity, fields)

        # Assert
        self.spies["tabulate"].assert_called_once_with(expected_list, headers=fields)
        tabulate_return = self.spies["tabulate"].return_value
        self.spies["ui"].assert_called_once_with(tabulate_return)
