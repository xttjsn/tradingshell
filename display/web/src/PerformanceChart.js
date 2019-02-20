import React from "react";
import PropTypes from "prop-types";

import { format } from "d3-format";
import { timeFormat } from "d3-time-format";

import { ChartCanvas, Chart } from "react-stockcharts";
import {
  LineSeries
} from "react-stockcharts/lib/series";
import { XAxis, YAxis } from "react-stockcharts/lib/axes";
import {
  EdgeIndicator,
  CrossHairCursor,
  MouseCoordinateY,
  MouseCoordinateX
} from "react-stockcharts/lib/coordinates";

import { discontinuousTimeScaleProvider } from "react-stockcharts/lib/scale";
import { HoverTooltip } from "react-stockcharts/lib/tooltip";
import { fitWidth } from "react-stockcharts/lib/helper";
import { last } from "react-stockcharts/lib/utils";

const dateFormat = timeFormat("%Y-%m-%d");
const numberFormat = format(".2f");

function tooltipContent(ys) {
  return ({ currentItem, xAccessor }) => {
    return {
      x: dateFormat(xAccessor(currentItem)),
      y: [
        {
          label: "val",
          value: currentItem.val && numberFormat(currentItem.val)
        }
      ]
        .concat(
          ys.map(each => ({
            label: each.label,
            value: each.value(currentItem),
            stroke: each.stroke
          }))
        )
        .filter(line => line.value)
    };
  };
}

const keyValues = ["val"];

class PerformanceChart extends React.Component {

  render() {
    let { type, data: initialData, width, ratio } = this.props;

    const margin = { left: 80, right: 80, top: 30, bottom: 50 };

    const xScaleProvider = discontinuousTimeScaleProvider.inputDateAccessor(
      d => d.date
    );
    const { data, xScale, xAccessor, displayXAccessor } = xScaleProvider(
      initialData
    );

    const start = xAccessor(last(data));
    const end = xAccessor(data[Math.max(0, data.length - 150)]);
    const xExtents = [start, end];

    return (
      <ChartCanvas
        height={400}
        width={width}
        ratio={ratio}
        margin={margin}
        type={type}
        seriesName="Performance Series"
        data={data}
        xScale={xScale}
        xAccessor={xAccessor}
        displayXAccessor={displayXAccessor}
        xExtents={xExtents}
      >
        <Chart
          id={1}
          yExtents={[d => [d.val]]}
          padding={{ top: 10, bottom: 20 }}
        >
          <XAxis axisAt="bottom" orient="bottom" />

          <YAxis axisAt="left" orient="left" ticks={10} />

          <LineSeries yAccessor={d => d.val}/>

          <CrossHairCursor />
          
          <MouseCoordinateX
            at="bottom"
            orient="bottom"
            displayFormat={timeFormat("%Y-%m-%d")} />
          
          <MouseCoordinateY
            at="left"
            orient="left"
            displayFormat={format(".4s")} />

          <EdgeIndicator
            itemType="last"
            orient="right"
            edgeAt="right"
            yAccessor={d => d.val}
            fill={d => ("#6BA583")}
          />

          <HoverTooltip
            yAccessor={d => d.val}
            tooltipContent={tooltipContent([])}
            fontSize={15}
          />
        </Chart>
      </ChartCanvas>
    );
  }
}

PerformanceChart.propTypes = {
  data: PropTypes.array.isRequired,
  width: PropTypes.number.isRequired,
  ratio: PropTypes.number.isRequired,
  type: PropTypes.oneOf(["svg", "hybrid"]).isRequired
};

PerformanceChart.defaultProps = {
  type: "svg"
};
PerformanceChart = fitWidth(PerformanceChart);

export default PerformanceChart;
