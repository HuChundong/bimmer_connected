"""Models state and remote services of one vehicle."""
from enum import Enum
import logging
from typing import TYPE_CHECKING

from bimmer_connected.state import VehicleState
from bimmer_connected.remote_services import RemoteServices
from bimmer_connected.const import VEHICLE_IMAGE_URL  # , SERVICE_CHARGING_PROFILE

if TYPE_CHECKING:
    from bimmer_connected.account import ConnectedDriveAccount

_LOGGER = logging.getLogger(__name__)


class DriveTrainType(Enum):
    """Different types of drive trains."""
    COMBUSTION = 'COMBUSTION'
    PLUGIN_HYBRID = 'PLUGIN_HYBRID'
    ELECTRIC = 'ELECTRIC'


#: Set of drive trains that have a combustion engine
COMBUSTION_ENGINE_DRIVE_TRAINS = {DriveTrainType.COMBUSTION, DriveTrainType.PLUGIN_HYBRID}

#: set of drive trains that have a high voltage battery
HV_BATTERY_DRIVE_TRAINS = {DriveTrainType.PLUGIN_HYBRID, DriveTrainType.ELECTRIC}


class VehicleViewDirection(Enum):
    """Viewing angles for the vehicle.

    This is used to get a rendered image of the vehicle.
    """
    FRONTSIDE = 'VehicleStatus'
    FRONT = 'VehicleInfo'
    # REARSIDE = 'REARSIDE'
    # REAR = 'REAR'
    SIDE = 'ChargingHistory'
    # DASHBOARD = 'DASHBOARD'
    # DRIVERDOOR = 'DRIVERDOOR'
    # REARBIRDSEYE = 'REARBIRDSEYE'


class LscType(Enum):
    """Known Values for lsc_type field.

    Not really sure, what this value really contains.
    """
    NOT_CAPABLE = 'NOT_CAPABLE'
    ACTIVATED = 'ACTIVATED'


class ConnectedDriveVehicle:
    """Models state and remote services of one vehicle.

    :param account: ConnectedDrive account this vehicle belongs to
    :param attributes: attributes of the vehicle as provided by the server
    """

    def __init__(self, account: "ConnectedDriveAccount", attributes: dict) -> None:
        self._account = account
        self.attributes = attributes
        self.state = VehicleState(account, attributes)
        self.remote_services = RemoteServices(account, self)
        self.observer_latitude = 0.0  # type: float
        self.observer_longitude = 0.0  # type: float

    def update_state(self) -> None:
        """Update the state of a vehicle."""
        self.state.update_data()

    @property
    def drive_train(self) -> DriveTrainType:
        """Get the type of drive train of the vehicle."""
        return DriveTrainType(self.attributes['driveTrain'])

    @property
    def name(self) -> str:
        """Get the name of the vehicle."""
        return self.attributes['model']

    @property
    def has_hv_battery(self) -> bool:
        """Return True if vehicle is equipped with a high voltage battery.

        In this case we can get the state of the battery in the state attributes.
        """
        return self.drive_train in HV_BATTERY_DRIVE_TRAINS

    @property
    def has_range_extender(self) -> bool:
        """Return True if vehicle is equipped with a range extender.

        In this case we can get the state of the gas tank."""
        return None
        # raise NotImplementedError("REX not specified explicitely, use ELECTRIC + fuel")
        # return self.drive_train in RANGE_EXTENDER_DRIVE_TRAINS

    @property
    def has_internal_combustion_engine(self) -> bool:
        """Return True if vehicle is equipped with an internal combustion engine.

        In this case we can get the state of the gas tank."""
        return self.drive_train in COMBUSTION_ENGINE_DRIVE_TRAINS

    @property
    def has_weekly_planner_service(self) -> bool:
        """Return True if charging control (weekly planner) is available."""
        # TODO: Check if chargingProfile should be own class
        return self.attributes["status"].get("chargingProfile", {}).get("chargingControlType") != "NOT_SUPPORTED"

    # @property
    # def drive_train_attributes(self) -> List[str]:
    #     """Get list of attributes available for the drive train of the vehicle.

    #     The list of available attributes depends if on the type of drive train.
    #     Some attributes only exist for electric/hybrid vehicles, others only if you
    #     have a combustion engine. Depending on the state of the vehicle, some of
    #     the attributes might still be None.
    #     """
    #     result = ['remaining_range_total', 'remaining_fuel', 'mileage']
    #     if self.has_hv_battery:
    #         result += ['charging_time_remaining', 'charging_status', 'max_range_electric', 'charging_level_hv',
    #                    'chargingConnectionType', 'chargingInductivePositioning', 'connectionStatus',
    #                    'lastChargingEndReason', 'remaining_range_electric', 'lastChargingEndResult']
    #     if self.has_internal_combustion_engine:
    #         result += ['remaining_range_fuel']
    #     if self.has_hv_battery and self.has_range_extender:
    #         result += ['maxFuel', 'remaining_range_fuel']
    #     if self.has_hv_battery and self.has_internal_combustion_engine:
    #         result += ['fuelPercent']
    #         result.remove('max_range_electric')
    #     return result

    @property
    def lsc_type(self) -> LscType:
        """Get the lscType of the vehicle.

        Not really sure what that value really means. If it is NOT_CAPABLE, that probably means that the
        vehicle state will not contain much data.
        """
        return LscType(self.attributes["capabilities"]["lastStateCall"].get('lscState'))

    # TODO: A new logic has be be implemented for available attributes
    #       Maybe we can keep the old logic, but now sure if this makes sense or not

    # @property
    # def available_attributes(self) -> List[str]:
    #     """Get the list of non-drivetrain attributes available for this vehicle."""
    #     # attributes available in all vehicles
    #     result = ['gps_position', 'steering', 'timestamp', 'vin']
    #     if self.lsc_type in [LscType.LSC_BASIS, LscType.I_LSC_IMM, LscType.LSC_PHEV]:
    #         # generic attributes if lsc_type =! NOT_SUPPORTED
    #         result += LIDS
    #         result += WINDOWS
    #         result += self.drive_train_attributes
    #         result += ['DCS_CCH_Activation', 'DCS_CCH_Ongoing', 'condition_based_services',
    #                    'check_control_messages', 'door_lock_state', 'internalDataTimeUTC',
    #                    'parking_lights', 'positionLight', 'last_update_reason', 'singleImmediateCharging']
    #         # required for existing Home Assistant binary sensors
    #         result += ['lids', 'windows']
    #         if self.has_parking_light_state:
    #             result += ['lights_parking']
    #     return result

    # TODO: We could probably implement this via vehicle_status.capabilities
    #       However currently not many endpoints are known.

    # @property
    # def available_state_services(self) -> List[str]:
    #     """Get the list of all available state services for this vehicle."""
    #     result = [SERVICE_PROPERTIES]

    #     if self.has_weekly_planner_service:
    #         result += [SERVICE_CHARGING_PROFILE]

    #     return result

    def get_vehicle_image(self, direction: VehicleViewDirection) -> bytes:
        """Get a rendered image of the vehicle.

        :returns bytes containing the image in PNG format.
        """
        url = VEHICLE_IMAGE_URL.format(
            vin=self.vin,
            server=self._account.server_url,
            view=direction.value,
        )
        header = self._account.request_header
        # the accept field of the header needs to be updated as we want a png not the usual JSON
        header['accept'] = 'image/png'
        response = self._account.send_request(url, headers=header)
        return response.content

    def __getattr__(self, item):
        """In the first version: just get the attributes from the dict.

        In a later version we might parse the attributes to provide a more advanced API.
        :param item: item to get, as defined in VEHICLE_ATTRIBUTES
        """
        return self.attributes.get(item)

    def __str__(self) -> str:
        """Use the name as identifier for the vehicle."""
        return '{}: {}'.format(self.__class__, self.name)

    def set_observer_position(self, latitude: float, longitude: float) -> None:
        """Set the position of the observer, who requests the vehicle state.

        Some vehicle require you to send your position to the server before you get the vehicle state.
        Your position must be within some range (2km?) of the vehicle to get you a proper answer.
        """
        if (latitude == 0.0 or longitude == 0.0) and latitude != longitude:
            raise ValueError('Either latitude AND longitude are set or none of them. You cannot set only one of them!')
        self.observer_latitude = latitude
        self.observer_longitude = longitude
