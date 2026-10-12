package com.efremandrei.photoforge3d;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.view.MotionEvent;
import android.view.View;
import org.json.JSONArray;
import java.util.ArrayList;
import java.util.Arrays;

public class MeshView extends View {
    private float[][] triangles = new float[0][];
    private float yaw=.6f,pitch=-.3f,lastX,lastY,zoom=1;
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    private boolean dark=true;
    public MeshView(Context c) { super(c); setContentDescription("3D surface preview. Drag to rotate."); }
    public void theme(boolean d) { dark=d; invalidate(); }
    public void mesh(JSONArray data) throws Exception {
        ArrayList<float[]> list=new ArrayList<>();
        int step=Math.max(1,(data.length()+1399)/1400);
        for(int i=0;i<data.length();i+=step) {
            float[] t=new float[9]; JSONArray tri=data.getJSONArray(i);
            for(int j=0;j<3;j++) for(int k=0;k<3;k++) t[j*3+k]=(float)tri.getJSONArray(j).getDouble(k);
            list.add(t);
        }
        triangles=list.toArray(new float[0][]);invalidate();
    }
    public void clear() { triangles=new float[0][];invalidate(); }
    @Override protected void onDraw(Canvas canvas) {
        canvas.drawColor(dark?0xff1c2838:0xffdce8f2);
        if(triangles.length==0) {
            paint.setColor(dark?0xffb6c7d7:0xff384d62);paint.setTextSize(15*getResources().getDisplayMetrics().scaledDensity);
            paint.setTextAlign(Paint.Align.CENTER);canvas.drawText("Your object, in 3D",getWidth()/2f,getHeight()/2f,paint);return;
        }
        float cy=(float)Math.cos(yaw),sy=(float)Math.sin(yaw),cp=(float)Math.cos(pitch),sp=(float)Math.sin(pitch);
        float scale=Math.min(getWidth(),getHeight())*.88f*zoom;
        float[][] transformed=new float[triangles.length][10];
        Integer[] order=new Integer[triangles.length];
        for(int i=0;i<triangles.length;i++) {
            order[i]=i;
            for(int j=0;j<3;j++) {
                float x=triangles[i][j*3],y=triangles[i][j*3+1],z=triangles[i][j*3+2];
                transformed[i][j*3]=(cy*x+sy*z)*scale+getWidth()/2f;
                transformed[i][j*3+1]=(sy*sp*x+cp*y-cy*sp*z)*scale+getHeight()/2f;
                transformed[i][9]+=-sy*cp*x+sp*y+cy*cp*z;
            }
        }
        Arrays.sort(order,(a,b)->Float.compare(transformed[a][9],transformed[b][9]));
        Path path=new Path();
        for(int i:order) {
            float[] t=transformed[i];path.reset();path.moveTo(t[0],t[1]);path.lineTo(t[3],t[4]);path.lineTo(t[6],t[7]);path.close();
            paint.setColor(0xff258f89);paint.setStyle(Paint.Style.FILL);canvas.drawPath(path,paint);
            paint.setColor(0xff50c4b0);paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(.6f);canvas.drawPath(path,paint);
        }
        paint.setStyle(Paint.Style.FILL);
        float[][] axes={{cy,sy*sp},{0,cp},{sy,-cy*sp}};
        int[] colors={0xfff68a86,0xff80dca9,0xff83b8ff};
        for(int i=0;i<3;i++) {
            float x=45+axes[i][0]*30,y=getHeight()-45+axes[i][1]*30;
            paint.setColor(colors[i]);paint.setStrokeWidth(2);canvas.drawLine(45,getHeight()-45,x,y,paint);
            paint.setTextSize(20);canvas.drawText("XYZ".substring(i,i+1),x,y-3,paint);
        }
    }
    @Override public boolean onTouchEvent(MotionEvent e) {
        if(e.getAction()==MotionEvent.ACTION_DOWN) { lastX=e.getX();lastY=e.getY();getParent().requestDisallowInterceptTouchEvent(true);return true; }
        if(e.getAction()==MotionEvent.ACTION_MOVE) { yaw+=(e.getX()-lastX)*.012;pitch+=(e.getY()-lastY)*.012;lastX=e.getX();lastY=e.getY();invalidate();return true; }
        if(e.getAction()==MotionEvent.ACTION_UP) { getParent().requestDisallowInterceptTouchEvent(false);performClick();return true; }
        return true;
    }
    @Override public boolean performClick() { super.performClick();return true; }
}
