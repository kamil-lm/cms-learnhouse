import { NodeViewContent, NodeViewWrapper } from "@tiptap/react";
import React from "react";
import styled from "styled-components";

function InfoCalloutComponent(props: any) {
  return (
    <NodeViewWrapper>
      <InfoCalloutWrapper contentEditable={props.extension.options.editable}>
      <div>⚠️ </div> <NodeViewContent contentEditable={props.extension.options.editable} className="content" />
      </InfoCalloutWrapper>
    </NodeViewWrapper>
  );
}

const InfoCalloutWrapper = styled.div`
  display: flex;
  flex-direction: row;
  background: #fefce8;
  color: #713f11;
  border: 1px solid #fff103;
  border-radius: 16px;
  margin: 1rem 0;
  align-items: center;
  padding-left: 15px;
  

  .content {
    margin: 5px;
    padding: 0.5rem;
    border: ${(props) => (props.contentEditable ? "2px dashed #713f1117" : "none")};
    border-radius: 0.5rem;
  }
`;

const DragHandle = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  width: 1rem;
  height: 100%;
  cursor: move;
  z-index: 1;
`;

export default InfoCalloutComponent;
