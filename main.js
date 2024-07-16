var data = undefined;

function plot() {
    let vizdiv = document.getElementById("vizdiv");

    vizdiv.innerHTML = "";

    if (data) {

        let r = document.getElementById("vizdiv").getBoundingClientRect();
        let h = r.height;
        let w = r.width;
        
        
        console.log("height=" + h + ",width=" + w);
        
        let spec = {
            '$schema': 'https://vega.github.io/schema/vega-lite/v5.6.1.json',
            'config': {'view': {'continuousWidth': 300, 'continuousHeight': 300}},
            'height': 400,
            'width': 900,
            'data': {"format":{"type":"csv"}, "values": data},
            'layer': [
                {
                    'mark': {'type': 'line'},
                    'encoding': {
                        'color': {
                            'field': 'season_year',
                            'legend': {'title': 'Season year'},
                            'type': 'nominal',
                            'scale': {"scheme":"tealblues"}
                        },
                        'opacity': {
                            'condition': {'param': 'year_select', 'value': 1}, 
                            'value': 0.05
                        },
                        'x': {
                            'field': 'month',
                            'scale': {
                                'domain': [
                                    'October',
                                    'November',
                                    'December',
                                    'January',
                                    'February',
                                    'March',
                                    'April'
                                ]
                            },
                            'title': 'Time Period',
                            'type': 'nominal',
                            'sort': {"field": "season_month"},
                        },
                        'y': {
                            'field': 'thickness',
                            'title': 'Mean thickness (m)',
                            'type': 'quantitative',
                            'scale': {
                                'domain': [0, 3.5]
                            }
                        }
                    },
                    'name': 'view_4',
                    'title': 'Mean sea ice thickness per year'
                },
                {
                    'mark': {'type': 'point'},
                    'encoding': {
                        'color': {
                            'field': 'season_year',
                            'legend': {'title': 'Season year'},
                            'type': 'nominal'
                        },
                        'opacity': {
                            'condition': {'param': 'year_select', 'value': 1}, 
                            'value': 0.05
                        },
                        'tooltip': [
                            {'field': 'thickness', 'type': 'quantitative'},
                            {'field': 'year', 'type': 'quantitative'},
                            {'field': 'month', 'type': 'nominal'}
                        ],
                        'x': {
                            'field': 'month',
                            'scale': {
                                'domain': [
                                    'October',
                                    'November',
                                    'December',
                                    'January',
                                    'February',
                                    'March',
                                    'April'
                                ]
                            },
                            'title': 'Time Period',
                            'type': 'nominal'
                        },
                        'y': {
                            'field': 'thickness',
                            'title': 'Mean thickness (m)',
                            'type': 'quantitative'
                        }
                    },
                'title': 'Mean sea ice thickness per year'}
            ],
            'params': [
                {
                    'name': 'year_select',
                    'select': {'type': 'point', 'fields': ['season_year']},
                    'bind': "legend",
                    'views': ['view_4']
                }
            ],
        };
        

        vegaEmbed(vizdiv, spec, {
            "theme": "quartz",
            "defaultStyle": false,
            "actions": {"export": true, "source": false, "compiled": false, "editor": false}
        });
    }
}

function main() {


    fetch("processed_files/time_series_data.csv").then(r => r.text()).then(txt => {
        data = txt;
        console.log(data);

        plot();

        window.addEventListener("resize", (evt) => { plot(); });

    });

}