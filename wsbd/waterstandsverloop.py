"""Module om eenvoudige waterstandverlopen te genereren op basis van superpositie van sinus-golven.
Doel: genereer een waterstandverloop op basis van 3 componenten:

1. Getij amplitude en faseverschil. De periode is 12u25 min
2. Amplitude storm en stormduur
3. Amplitude afvoergolf en duur afvoergolf

Het waterstandverloop is een superpositie van deze drie componenten. De top van de storm en de top van de afvoergolf komen overeen. Voor de getijdebeweging kan een faseverschil worden gedefinieerd, bijvoorbeeld -6 uur (de getijdebeweging is 6 uur voor de top van de storm).

Alle componenten worden beschreven door een sinus.
Op t = 0 is de top van de afvoergolf en de stormcomponent.
"""

from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt

@dataclass
class ComponentWaterstandsVerloop:
    """Class om het waterstandsverloop over de tijd te beschrijven voor een specifieke component (afvoergolf, stormopzet).
    """
    component: str  # component name (e.g., 'afvoergolf' 'stormopzet')
    stormduur: float # stormduur in seconden
    amplitude: float # amplitude in meter
    dt : float = 1.0  # time step in seconds

    @property
    def periode(self):
        """Bereken de periode van het waterstandsverloop."""
        return 2 * self.stormduur

    def generate_waterstandsverloop(self, tijdreeks: None | np.ndarray = None) -> tuple[np.ndarray, np.ndarray]:
        """Bereken de waterstand op basis van de tijdreeks.
        Controleer of de waarden in de teruggegeven array tussen 0.0 en amplitude liggen. Zo niet, stel de waarden in op 0.0 in de teruggegeven array.
        Stel ook ws in op 0.0 buiten de stormduur.
        """
        if tijdreeks is None:
            tijdreeks = np.arange(-(self.stormduur+self.dt)/2, (self.stormduur+self.dt)/2, self.dt)
        
        # Calculate waterstand
        ws = self.amplitude * np.cos(2 * np.pi * tijdreeks / self.periode)
        
        # Mask: only within stormduur
        binnen_stormduur = (tijdreeks >= -self.stormduur/2) & (tijdreeks <= self.stormduur/2)
        # Mask: only values between 0.0 and amplitude
        binnen_amplitude = (ws >= 0.0) & (ws <= self.amplitude)
        # Combine both masks
        mask = binnen_stormduur & binnen_amplitude
        ws_checked = np.where(mask, ws, 0.0)
        return tijdreeks, ws_checked

    def plot(self):
        tijdreeks, waterstandsverloop = self.generate_waterstandsverloop()
        plt.figure(figsize=(10, 5))
        plt.plot(tijdreeks / 3600.0, waterstandsverloop, label=self.component)
        plt.xlabel('Tijd (uur)')
        plt.ylabel('Amplitude (m)')
        plt.title(self.component)
        plt.grid()
        plt.show()


@dataclass
class GetijdeVerloop:
    """Class om de getijdebeweging te beschrijven."""
    periode: float # periode in seconden
    amplitude: float # amplitude in meter
    faseverschuiving: float = 0.0  # faseverschuiving in seconden
    dt: float = 1.0
    
    def generate_waterstandsverloop(self, tijdreeks: None | np.ndarray = None) -> tuple[np.ndarray, np.ndarray]:
        """Bereken de getijdewaterstand op basis van de tijdreeks.
        Controleer of de waarden in de teruggegeven array tussen 0.0 en amplitude liggen. Zo niet, stel de waarden in op 0.0 in de teruggegeven array.
        """
        if tijdreeks is None:
            tijdreeks = np.arange(-(2.0*self.periode+self.dt), (2.0*self.periode+self.dt), self.dt)
        ws = self.amplitude * np.cos(2 * np.pi * (tijdreeks - self.faseverschuiving) / self.periode)
        return tijdreeks, ws

    def plot(self):
        tijdreeks, ws = self.generate_waterstandsverloop()
        plt.figure(figsize=(10, 5))
        plt.plot(tijdreeks / 3600.0, ws, label='getijde')
        plt.xlabel('Tijd (uur)')
        plt.ylabel('Amplitude (m)')
        plt.title('Getijde waterstand over de tijd')
        plt.grid()
        plt.show()

@dataclass
class WaterstandsVerloop:
    """Class to represent the superposition of water levels from different components."""
    afvoergolf: ComponentWaterstandsVerloop
    stormopzet: ComponentWaterstandsVerloop
    getijde: GetijdeVerloop
    dt: float = 1.0

    @property
    def max_stormduur(self):
        """Calculate the maximum storm duration from the components."""
        return max(self.afvoergolf.stormduur, self.stormopzet.stormduur)
    
    @property
    def tijdreeks_waterstandsverloop(self):
        """Generate a time series that covers the entire duration of the water level evolution. Based on stormduur of afvoergolf and stormopzet."""
        # Determine the start and end times based on the components
        # Ensure that the time series covers the entire duration of all components
        return np.arange(-(self.max_stormduur+self.dt)/2, (self.max_stormduur+self.dt)/2, self.dt)

    def generate_waterstandsverloop(self):
        """Generate the combined water level evolution and a normalised version."""
        # Generate the time series for each component based on the generated time series of this class
        tijdreeks = self.tijdreeks_waterstandsverloop
        _, ws_afvoergolf = self.afvoergolf.generate_waterstandsverloop(tijdreeks)
        _, ws_stormopzet = self.stormopzet.generate_waterstandsverloop(tijdreeks)
        # Get the tidal water level evolution
        _, ws_getijde = self.getijde.generate_waterstandsverloop(tijdreeks)

        # Superposition of water levels
        waterstandsverloop = ws_getijde + ws_afvoergolf + ws_stormopzet
        max_abs = np.max(np.abs(waterstandsverloop))
        normalised_waterstandsverloop = (
            waterstandsverloop / max_abs if max_abs != 0 else np.zeros_like(waterstandsverloop)
        )
        return tijdreeks, waterstandsverloop, normalised_waterstandsverloop
   
    
    # Plot the combined water level evolution
    def plot(self, normalised: bool = False):
        tijdreeks, waterstandsverloop, normalised_waterstandsverloop = self.generate_waterstandsverloop()
        plt.figure(figsize=(10, 5))
        if normalised:
            plt.plot(tijdreeks / 3600.0, normalised_waterstandsverloop, label='Genormaliseerd waterstandsverloop', color='blue')
        else:
            plt.plot(tijdreeks / 3600.0, waterstandsverloop, label='Waterstandsverloop', color='green')
        plt.xlabel('Tijd (uur)')
        plt.ylabel('Waterstand (m)')
        plt.title('Gecombineerd waterstandsverloop')
        plt.grid()
        plt.legend()
        plt.show()