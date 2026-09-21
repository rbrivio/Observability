from astroplan import Observer, FixedTarget
from astroplan.plots import plot_altitude
from astropy.time import Time
from astropy.coordinates import SkyCoord, get_sun, get_moon, EarthLocation
import astropy.units as u
from datetime import timedelta
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cm as cm

observatories = {'La Silla': 'lasilla', 'Paranal': 'paranal', 'La Palma': 'lapalma', 'LBT': 'lbt', 'Gemini-North': 'Gemini North', 'Gemini-South': 'Gemini South', 'Cerro Tololo':'lco'}
custom_sites = {'LBT': Observer(
            location=EarthLocation(
            lat=32.7013*u.deg,
            lon=-109.8891*u.deg,
            height=3191*u.m),
            name='LBT',
            timezone='US/Arizona'),
        'Gemini-North': Observer(
            location=EarthLocation(
            lat=19.8238*u.deg,
            lon=-155.4691*u.deg,
            height=4213*u.m),
            name='Gemini North',
            timezone='US/Hawaii')}

def safe_time(t):
    return None if t.mask else t

def coords_conv(ra_input, dec_input):
    if ra_input.find(':') != -1:
        coord = SkyCoord(ra=ra_input, dec=dec_input, frame='icrs', unit=(u.hourangle, u.deg))
    elif ra_input.find(':') == -1:
        coord = SkyCoord(ra=ra_input, dec=dec_input, frame='icrs', unit=(u.deg, u.deg))

    return coord

def airmass(elev_deg):
    elev_deg = np.clip(elev_deg, 0.1, 90)
    return 1 / (np.sin(np.radians(elev_deg)) + 0.50572 * (elev_deg + 6.07995)**-1.6364)

def do_plot (ax,xlbl="",ylbl="",title="",ylbl_right="",linwidth=2,tickxfonsiz=15,tickyfonsiz=15,xlblfonsiz=20,ylblfonsiz=20,titlefonsiz=25,titlepad=20,right=False,top=False):
    # Lines
    [i.set_linewidth(linwidth) for i in ax.spines.values()]
    # Ticks
    ax.tick_params(axis='both', which='major', direction='in', top=top, right=right, labelsize='xx-large',width=1,length=8)
    ax.tick_params(axis='both', which='minor', direction='in', top=top, right=right, labelsize='x-large',width=1,length=5,pad=8)
    #
    for tickx,ticky in zip(ax.xaxis.get_major_ticks(),ax.yaxis.get_major_ticks()):
        tickx.label1.set_fontsize(tickxfonsiz) 
        ticky.label1.set_fontsize(tickyfonsiz)
    # Labels
    ax.set_xlabel(xlbl,fontsize=xlblfonsiz)
    ax.set_ylabel(ylbl,fontsize=ylblfonsiz)
    ax.set_title(title,fontsize=titlefonsiz,pad=titlepad)

def plot_source(ax, ra_input,dec_input, observer, times, moon_altaz, target_name, color):
    
    # Prepare quantities for plot
    target_coord = coords_conv(ra_input, dec_input)
    target = FixedTarget(name=target_name, coord=target_coord)

    altaz = observer.altaz(times, target)
    altitudes = altaz.alt
    moon_distance = altaz.separation(moon_altaz).deg

    plot_altitude(target, observer, times, ax=ax, style_kwargs={'color':color,'linewidth':3,'linestyle':'-','marker':''})

    moon_degs = []
    for t,md,alt in zip(times[::25],moon_distance[::25],altitudes[::25]):
        ann = ax.annotate(f"{md:.1f}°", (t.datetime, alt.to_value(u.deg)), textcoords="offset points", xytext=(0,15), ha="center", fontsize=10, c=color)
        moon_degs.append(ann)
    #ax.annotate(f"{target_name}", (times[0].datetime,altitudes[0].to_value(u.deg)), textcoords="offset points", xytext=(0,15), ha="center", fontsize=10, c='green')
    
    line = ax.get_lines()[-1]
    line.set_picker(5)
    line.set_zorder(10)
    line.set_gid(target_name)

    return moon_degs

def plot_observability(ax, site, ra_input, dec_input, target_names=[], date='today'):
    
    colors = cm.tab10(np.linspace(0, 1, len(ra_input)))
    if date == 'today':
        date = Time.now().to_value('iso', subfmt='date')

    do_plot(ax,f'Time [UTC]','Altitude [deg]',f'Visibility on {date} (UTC) at {site}',titlefonsiz=22)

    #start_time = Time(f'{date} 20:00:00')  # UTC noon
    #end_time = start_time + 24 * u.hour
    start_time = Time(date) - 12*u.hour
    end_time = Time(date) + 12*u.hour
    times = start_time + np.linspace(0, 24, 300) * u.hour

    if not site in ('La Silla', 'Paranal', 'La Palma', 'LCO', 'Gemini-North', 'Gemini-South', 'LBT'):
        raise ValueError("Invalid site provided. Admitted values: 'LaSilla', 'Paranal', 'LaPalma', 'LCO', 'Gemini-North', 'Gemini-South', 'LBT'")

    if site in custom_sites:
        observer = custom_sites[site]
    else:
        observer = Observer.at_site(observatories[site])

    # Compute sun coordinates
    sun_coords = get_sun(times)
    sun_altaz = observer.altaz(times, sun_coords)
    sun_alt = sun_altaz.alt

    # Compute exact twilight times
    sunset = observer.sun_set_time(start_time, which='next')
    sunrise = observer.sun_rise_time(sunset, which='next')
    civil_twilight_start = observer.twilight_evening_civil(sunset, which='nearest')
    civil_twilight_end = observer.twilight_morning_civil(sunrise, which='nearest')
    
    # Get moon distance
    moon_coords = get_moon(times, observer.location)
    moon_target = FixedTarget(name='Moon', coord=moon_coords)
    moon_altaz = observer.altaz(times, get_moon(times, observer.location))

    airmass_vals = [airmass(alt) for alt in np.arange(10,100,10)]
    ax_right = ax.twinx()
    ax_right.set_zorder(0)
    ax.set_zorder(1)
    ax.patch.set_visible(False)
    ax_right.set_yticks(np.arange(10, 100, 10))
    ax_right.set_yticklabels([f"{airmass(alt):.2f}" for alt in np.arange(10, 100, 10)])
    ax_right.set_ylabel('Airmass', fontsize=20)
    ax_right.tick_params(axis='both', which='major', direction='in', labelsize='xx-large',width=1,length=8)
    ax_right.tick_params(axis='both', which='minor', direction='in', labelsize='x-large',width=1,length=5,pad=8)
    for ticky_r in ax_right.yaxis.get_major_ticks():
        ticky_r.label1.set_fontsize(15)

    ax.axhline(30, color='gray', linestyle=':', alpha=0.6)
    ax.axhline(20, color='gray', linestyle='--', alpha=0.4)

    # Add vertical lines for sunset and sunrise
    for time, color, label in zip([sunset, sunrise], ['orangered','orange'], ['Sunset', 'Sunrise']):
        ax.axvline(time.datetime, color=color, linestyle='--')
        ax.annotate(f"{time.ymdhms[3]}:{time.ymdhms[4]}", (time.datetime+timedelta(minutes=12),75), ha="center", fontsize='medium', c=color, rotation=90)
        ax.annotate(label, (time.datetime+timedelta(minutes=12),1.02), va="bottom", xycoords=("data", "axes fraction"), ha="center", fontsize='medium', c=color, rotation=0)

    # Ensure evening and morning are ok
    astro_start = safe_time(observer.twilight_evening_astronomical(sunset, which='nearest'))
    astro_end = safe_time(observer.twilight_morning_astronomical(sunrise, which='nearest'))
    civil_start = safe_time(observer.twilight_evening_civil(sunset, which='nearest'))
    civil_end = safe_time(observer.twilight_morning_civil(sunrise, which='nearest'))

    if astro_start and astro_end:
        ax.axvspan(astro_start.datetime,astro_end.datetime,
            color='navy', alpha=0.1) #, label='Astronomical twilight')
        ax.annotate(f"{astro_start.ymdhms[3]:02d}:{astro_start.ymdhms[4]:02d}",(astro_start.datetime - timedelta(minutes=12), 75),
                    ha="center", fontsize='medium', color='blue', rotation=90)
        ax.annotate(f"{astro_end.ymdhms[3]:02d}:{astro_end.ymdhms[4]:02d}",(astro_end.datetime + timedelta(minutes=12), 75),
                    ha="center", fontsize='medium', color='blue', rotation=90)
    if civil_start and civil_end:
        ax.axvspan(civil_start.datetime,civil_end.datetime,
            color='lightblue', alpha=0.3) #, label='Civil twilight')

    # Plot altitude vs. time
    moon_degs = {}
    for ra,dec,target_name,color in zip(ra_input,dec_input,target_names,colors):
        annotations = plot_source(ax, ra,dec, observer, times, moon_altaz, target_name,color)
        moon_degs[target_name] = annotations

    plot_altitude(moon_target, observer, times, ax=ax, style_kwargs={'color':'blue','linewidth':1.5,'linestyle':'--','marker':''})

    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), ncol=2, fontsize='medium', loc='lower right', framealpha=1, edgecolor='black')

    ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    ax.xaxis.set_minor_locator(mdates.HourLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    ax.set_xlim(civil_twilight_start.datetime - timedelta(hours=2), civil_twilight_end.datetime + timedelta(hours=2))
    ax.set_ylim(0,90)
    
    ax.figure.tight_layout()

    return moon_degs
